"""MTB-Evo pipeline core class with optimized implementation."""

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config import PipelineConfig
from src.exceptions import (
    FileNotFoundError,
    MTBEvoError,
    PipelineError,
    ToolNotFoundError,
)
from src.utils.logging_config import setup_logging
from src.utils.tools import ToolManager


class MTBPipeline:
    """MTB-Evo analysis pipeline with daemon mode support."""
    
    def __init__(
        self,
        samples: Path,
        output_dir: Path = Path("results"),
        threads: int = 4,
        sort_threads: int = 2,
        verbose: bool = False
    ):
        """Initialize pipeline.
        
        Args:
            samples: Path to sample list file
            output_dir: Output directory path
            threads: Number of threads for bowtie2
            sort_threads: Number of threads for samtools sort
            verbose: Enable debug logging
        """
        self.samples = samples.absolute()
        self.output_dir = output_dir.absolute()
        self.threads = threads
        self.sort_threads = sort_threads
        self.verbose = verbose
        
        # 计算项目根目录
        self.script_dir = Path(__file__).parent.parent.parent
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.output_dir / f"run_all_{timestamp}.log"
        
        # Initialize logging (will be set up after daemonize)
        self.logger = None
        
        # Initialize tool manager
        self.tool_manager = ToolManager()
    
    def setup_logging(self, console_output: bool = True):
        """Setup logging after daemonize."""
        self.logger = setup_logging(
            log_file=self.log_file,
            verbose=self.verbose,
            console_output=console_output
        )
    
    def daemonize(self):
        """Daemonize the process using double-fork technique."""
        # First fork
        try:
            pid = os.fork()
            if pid > 0:
                # Parent process: print message and exit
                print(f"Pipeline started, check logs at: {self.log_file}")
                sys.exit(0)
        except OSError as e:
            print(f"Failed to fork: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Child process
        os.chdir(self.output_dir)
        os.setsid()
        os.umask(0)
        
        # Second fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            print(f"Failed to fork: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Grandchild process (actual daemon)
        sys.stdout.flush()
        sys.stderr.flush()
        
        with open('/dev/null', 'r') as f:
            os.dup2(f.fileno(), sys.stdin.fileno())
        with open('/dev/null', 'a+') as f:
            os.dup2(f.fileno(), sys.stdout.fileno())
            os.dup2(f.fileno(), sys.stderr.fileno())
        
        # Setup logging in daemon (no console output)
        self.setup_logging(console_output=False)
    
    def _ensure_logger(self):
        """Ensure logger is initialized."""
        if self.logger is None:
            self.setup_logging(console_output=True)
    
    def validate_inputs(self) -> bool:
        """Validate all required inputs."""
        self._ensure_logger()
        
        if not self.samples.exists():
            raise FileNotFoundError(f"Sample list not found: {self.samples}")
        
        # Validate tools
        if not self.tool_manager.validate_all():
            missing = self.tool_manager.check_required()
            raise ToolNotFoundError(missing)
        
        return True
    
    def run_step1(self):
        """Step 1: Generate SNP calling script."""
        self._ensure_logger()
        self.logger.info("[1/8] Step 1: Generating SNP calling script...")
        
        pair_script = self.script_dir / "src" / "scripts" / "pair_fixed_nostrandbias.py"
        
        if not pair_script.exists():
            raise FileNotFoundError(f"Script not found: {pair_script}")
        
        self.logger.debug(f"Using script: {pair_script}")
        self.logger.debug(f"Using samples: {self.samples}")
        
        cmd = [
            "python3",
            str(pair_script),
            str(self.samples),
            "--threads", str(self.threads),
            "--sort-threads", str(self.sort_threads)
        ]
        
        process = None
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                cwd=self.script_dir
            )
            
            stdout, stderr = process.communicate(input='y\n', timeout=600)
            
            if process.returncode != 0:
                raise PipelineError(
                    f"Script failed with return code {process.returncode}",
                    step=1,
                    details={"stderr": stderr, "stdout": stdout}
                )
            
            # Log stdout
            if stdout:
                for line in stdout.strip().split('\n'):
                    if line.strip():
                        self.logger.debug(f"  {line}")
            
            self.logger.info("  ✓ Generated: results/pair_end.sh")
            
            # Count samples
            with open(self.samples) as f:
                strain_count = len([line for line in f if line.strip()])
            self.logger.info(f"  ✓ Found {strain_count} strains to process")
            
        except subprocess.TimeoutExpired:
            if process:
                process.kill()
            raise PipelineError("Script execution timeout (>10 minutes)", step=1)
        except subprocess.CalledProcessError as e:
            raise PipelineError(f"Script failed: {e}", step=1) from e
    
    def run_step2_daemon(self):
        """Step 2: Run SNP calling as daemon."""
        self._ensure_logger()
        self.logger.info("[2/8] Step 2: Running SNP calling (daemon mode)")
        
        script_path = self.output_dir / "pair_end.sh"
        log_path = self.output_dir / "pair_end.log"
        
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        
        # Check if already running
        result = subprocess.run(
            ["pgrep", "-f", "pair_end.sh"],
            capture_output=True
        )
        
        if result.returncode == 0:
            self.logger.warning("  SNP calling is already running")
        else:
            # Start as daemon
            with open(log_path, "w") as log_file:
                subprocess.Popen(
                    ["nohup", "bash", str(script_path)],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    cwd=self.script_dir,
                    start_new_session=True
                )
            self.logger.info(f"  ✓ Started daemon: {script_path}")
        
        self.logger.info(f"  Log file: {log_path}")
        self.logger.info("  This step may take 2-4 hours.")
    
    def check_step2_complete(self, expected_count: int) -> bool:
        """Check if Step 2 is complete by counting .snp files."""
        snp_files = list(self.output_dir.glob("*.snp"))
        return len(snp_files) >= expected_count
    
    def monitor_step2(self, expected_count: int):
        """Monitor Step 2 progress until completion."""
        self._ensure_logger()
        self.logger.info("Monitoring Step 2 progress...")
        self.logger.info("  This may take 2-4 hours.")
        
        start_time = time.time()
        last_count = 0
        
        while not self.check_step2_complete(expected_count):
            snp_files = list(self.output_dir.glob("*.snp"))
            current_count = len(snp_files)
            
            if current_count > last_count:
                elapsed = (time.time() - start_time) / 60
                self.logger.info(
                    f"  Progress: {current_count}/{expected_count} samples "
                    f"completed ({elapsed:.1f} min)"
                )
                last_count = current_count
            
            time.sleep(60)
        
        elapsed = (time.time() - start_time) / 60
        self.logger.info(f"  ✓ Step 2 completed! ({elapsed:.1f} min)")
        self.logger.info("  Continuing with Steps 3-8...")
    
    def run_step3(self):
        """Step 3: Extract differential loci."""
        self._ensure_logger()
        self.logger.info("[3/8] Step 3: Extracting differential loci...")
        from src.commands.diff_loci import diff_loci_cmd
        diff_loci_cmd(Path("."), Path("diff_loci.txt"))
        self.logger.info("  ✓ Step 3 completed")
    
    def run_step4(self):
        """Step 4: Recall genotypes."""
        self._ensure_logger()
        self.logger.info("[4/8] Step 4: Recalling genotypes...")
        from src.commands.recall import recall_genotype
        
        cns_files = list(Path(".").glob("*.cns"))
        if not cns_files:
            self.logger.warning("  No CNS files found")
            return
        
        for i, cns_file in enumerate(cns_files, 1):
            output_name = cns_file.stem.replace(".cns", "") + ".recall.fasta"
            try:
                recall_genotype(Path("diff_loci.txt"), None, cns_file, Path(output_name))
                self.logger.info(f"  ✓ [{i}/{len(cns_files)}] {cns_file.name}")
            except Exception as e:
                self.logger.error(f"  ✗ [{i}/{len(cns_files)}] {cns_file.name}: {e}")
                raise PipelineError(f"Failed to recall {cns_file.name}", step=4) from e
    
    def run_step5(self):
        """Step 5: Merge sequences."""
        self._ensure_logger()
        self.logger.info("[5/8] Step 5: Merging sequences...")
        from src.commands.merge import merge_cmd
        merge_cmd(Path("."), Path("merged.fasta"))
        self.logger.info("  ✓ Step 5 completed")
    
    def run_step6(self):
        """Step 6: Extract wild-type bases."""
        self._ensure_logger()
        self.logger.info("[6/8] Step 6: Extracting wild-type bases...")
        from src.commands.wild_extract import wild_extract_cmd
        
        ancestor = Path("../data/tb.ancestor.fasta")
        if not ancestor.exists():
            ancestor = Path("data/tb.ancestor.fasta")
        
        wild_extract_cmd(Path("diff_loci.txt"), ancestor, Path("wildtype.fasta"))
        self.logger.info("  ✓ Step 6 completed")
    
    def run_step7(self):
        """Step 7: Filter core SNPs."""
        self._ensure_logger()
        self.logger.info("[7/8] Step 7: Filtering core SNPs...")
        from src.commands.filter import filter_cmd
        filter_cmd(Path("wildtype.fasta"), Path("merged.fasta"), 5, "core_snps")
        self.logger.info("  ✓ Step 7 completed")
    
    def run_step8(self):
        """Step 8: Calculate pairwise distances."""
        self._ensure_logger()
        self.logger.info("[8/8] Step 8: Calculating pairwise distances...")
        from src.commands.distance import distance_cmd
        
        bak_files = list(Path(".").glob("*.bak.fa"))
        if bak_files:
            distance_cmd(bak_files[0], Path("distance_matrix.txt"))
            self.logger.info("  ✓ Step 8 completed")
        else:
            self.logger.warning("  No filtered alignment file found")
    
    def run_all(self):
        """Run complete pipeline with error handling."""
        try:
            # Validate inputs
            self.validate_inputs()
            
            # Get expected sample count
            with open(self.samples) as f:
                expected_samples = len([line for line in f if line.strip()])
            
            # Run steps
            self.run_step1()
            self.run_step2_daemon()
            self.monitor_step2(expected_samples)
            
            # Change to output directory for remaining steps
            os.chdir(self.output_dir)
            
            self.run_step3()
            self.run_step4()
            self.run_step5()
            self.run_step6()
            self.run_step7()
            self.run_step8()
            
            # Summary
            self.logger.info("=" * 60)
            self.logger.info("🎉 Analysis completed successfully!")
            self.logger.info("=" * 60)
            self.logger.info(f"Results saved in: {self.output_dir}/")
            self.logger.info("Key output files:")
            self.logger.info("  • Core SNP alignment: *.bak.fa")
            self.logger.info("  • Distance matrix: distance_matrix.txt")
            self.logger.info("  • SNP results: *.snp files")
            
        except MTBEvoError as e:
            # 优雅处理已知错误
            if self.logger:
                self.logger.error(f"Pipeline failed: {e}")
            else:
                print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            # 未知错误，记录详细信息
            if self.logger:
                self.logger.exception("Unexpected error occurred")
            else:
                print(f"Unexpected error: {e}", file=sys.stderr)
            sys.exit(1)
