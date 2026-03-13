"""MTB-Evo pipeline core class."""

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


class MTBPipeline:
    """MTB-Evo analysis pipeline with daemon mode support."""
    
    def __init__(self, samples: Path, output_dir: Path, threads: int = 4, sort_threads: int = 2):
        """Initialize pipeline.
        
        Args:
            samples: Path to sample list file
            output_dir: Output directory path
            threads: Number of threads for bowtie2
            sort_threads: Number of threads for samtools sort
        """
        self.samples = samples.absolute()
        self.output_dir = output_dir.absolute()
        self.threads = threads
        self.sort_threads = sort_threads
        self.script_dir = Path(__file__).parent.parent.parent.parent
        self.log_file = None
        self.log_f = None
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup log file path (before any chdir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.output_dir / f"run_all_{timestamp}.log"
    
    def _log(self, message: str):
        """Write message to log file."""
        if self.log_f:
            self.log_f.write(message + "\n")
            self.log_f.flush()
    
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
        os.setsid()  # Create new session
        os.umask(0)
        
        # Second fork to prevent zombie processes
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            print(f"Failed to fork: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Grandchild process (actual daemon)
        # Redirect stdio to /dev/null
        sys.stdout.flush()
        sys.stderr.flush()
        
        with open('/dev/null', 'r') as f:
            os.dup2(f.fileno(), sys.stdin.fileno())
        with open('/dev/null', 'a+') as f:
            os.dup2(f.fileno(), sys.stdout.fileno())
            os.dup2(f.fileno(), sys.stderr.fileno())
        
        # Open log file in daemon
        if self.log_file is not None:
            self.log_f = open(self.log_file, 'w')
    
    def check_tools(self):
        """Check if required tools are available."""
        tools = ["sickle", "bowtie2", "samtools", "java"]
        missing = []
        for tool in tools:
            result = subprocess.run(
                ["which", tool],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                missing.append(tool)
        return missing
    
    def run_step1(self):
        """Step 1: Generate SNP calling script."""
        self._log("[1/8] Step 1: Generating SNP calling script...")
        
        missing = self.check_tools()
        if missing:
            self._log(f"Missing tools: {', '.join(missing)}")
            self._log("Please activate conda environment: conda activate mtb-evo")
            sys.exit(1)
        
        pair_script = self.script_dir / "scripts" / "pair_fixed_nostrandbias.py"
        
        if not pair_script.exists():
            self._log(f"Script not found: {pair_script}")
            sys.exit(1)
        
        if not self.samples.exists():
            self._log(f"Sample list not found: {self.samples}")
            sys.exit(1)
        
        self._log(f"  Using script: {pair_script}")
        self._log(f"  Using samples: {self.samples}")
        
        cmd = [
            "python3", 
            str(pair_script),
            str(self.samples),
        ]
        
        if self.threads:
            cmd.extend(["--threads", str(self.threads)])
        if self.sort_threads:
            cmd.extend(["--sort-threads", str(self.sort_threads)])
        
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
                self._log(f"Script failed with error:")
                self._log(stderr)
                sys.exit(1)
            
            if stdout:
                for line in stdout.split('\n'):
                    if line.strip():
                        self._log(f"    {line}")
            
            self._log("  Generated: results/pair_end.sh")
            self._log("  Tools detected: sickle, bowtie2, samtools, java, VarScan")
            
            with open(self.samples) as f:
                strain_count = len([line for line in f if line.strip()])
            self._log(f"  Found {strain_count} strains to process")
            
        except subprocess.TimeoutExpired:
            self._log("Timeout: Script took too long (>10 minutes)")
            if process:
                process.kill()
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            self._log(f"Failed to generate script: {e}")
            sys.exit(1)
    
    def run_step2_daemon(self):
        """Step 2: Run SNP calling as daemon."""
        self._log("\n[2/8] Step 2: Running SNP calling (daemon mode)")
        
        script_path = self.output_dir / "pair_end.sh"
        log_path = self.output_dir / "pair_end.log"
        
        if not script_path.exists():
            self._log(f"Script not found: {script_path}")
            sys.exit(1)
        
        # Check if already running
        result = subprocess.run(
            ["pgrep", "-f", "pair_end.sh"],
            capture_output=True
        )
        
        if result.returncode == 0:
            self._log("  SNP calling is already running")
        else:
            # Start as daemon using nohup
            with open(log_path, "w") as log_file:
                subprocess.Popen(
                    ["nohup", "bash", str(script_path)],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    cwd=self.script_dir,
                    start_new_session=True
                )
            self._log(f"  Started daemon: {script_path}")
        
        self._log(f"  Log file: {log_path}")
        self._log("  This step may take 2-4 hours.")
    
    def check_step2_complete(self, expected_count: int) -> bool:
        """Check if Step 2 is complete by counting .snp files."""
        snp_files = list(self.output_dir.glob("*.snp"))
        return len(snp_files) >= expected_count
    
    def monitor_step2(self, expected_count: int):
        """Monitor Step 2 progress until completion."""
        self._log("\nMonitoring Step 2 progress...")
        self._log("   This may take 2-4 hours.")
        
        start_time = time.time()
        last_count = 0
        
        while not self.check_step2_complete(expected_count):
            snp_files = list(self.output_dir.glob("*.snp"))
            current_count = len(snp_files)
            
            if current_count > last_count:
                elapsed = (time.time() - start_time) / 60
                self._log(f"   Progress: {current_count}/{expected_count} samples completed ({elapsed:.1f} min)")
                last_count = current_count
            
            time.sleep(60)
        
        elapsed = (time.time() - start_time) / 60
        self._log(f"  Step 2 completed! ({elapsed:.1f} min)")
        self._log("  Continuing with Steps 3-8...\n")
    
    def run_step3(self):
        """Step 3: Extract differential loci."""
        self._log("[3/8] Step 3: Extracting differential loci...")
        from src.commands.diff_loci import diff_loci_cmd
        diff_loci_cmd(Path("."), Path("diff_loci.txt"))
    
    def run_step4(self):
        """Step 4: Recall genotypes."""
        self._log("\n[4/8] Step 4: Recalling genotypes...")
        from src.commands.recall import recall_genotype
        cns_files = list(Path(".").glob("*.cns"))
        for cns_file in cns_files:
            output_name = cns_file.stem.replace(".cns", "") + ".recall.fasta"
            recall_genotype(Path("diff_loci.txt"), None, cns_file, Path(output_name))
    
    def run_step5(self):
        """Step 5: Merge sequences."""
        self._log("\n[5/8] Step 5: Merging sequences...")
        from src.commands.merge import merge_cmd
        merge_cmd(Path("."), Path("merged.fasta"))
    
    def run_step6(self):
        """Step 6: Extract wild-type bases."""
        self._log("\n[6/8] Step 6: Extracting wild-type bases...")
        from src.commands.wild_extract import wild_extract_cmd
        ancestor = Path("../data/tb.ancestor.fasta")
        if not ancestor.exists():
            ancestor = Path("data/tb.ancestor.fasta")
        wild_extract_cmd(Path("diff_loci.txt"), ancestor, Path("wildtype.fasta"))
    
    def run_step7(self):
        """Step 7: Filter core SNPs."""
        self._log("\n[7/8] Step 7: Filtering core SNPs...")
        from src.commands.filter import filter_cmd
        filter_cmd(Path("wildtype.fasta"), Path("merged.fasta"), 5, "core_snps")
    
    def run_step8(self):
        """Step 8: Calculate pairwise distances."""
        self._log("\n[8/8] Step 8: Calculating pairwise distances...")
        from src.commands.distance import distance_cmd
        bak_files = list(Path(".").glob("*.bak.fa"))
        if bak_files:
            distance_cmd(bak_files[0], Path("distance_matrix.txt"))
        else:
            self._log("  No filtered alignment file found")
    
    def run_all(self):
        """Run complete pipeline."""
        try:
            with open(self.samples) as f:
                expected_samples = len([line for line in f if line.strip()])
            
            # Step 1
            self.run_step1()
            
            # Step 2 (daemon)
            self.run_step2_daemon()
            
            # Wait for Step 2
            self.monitor_step2(expected_samples)
            
            # Change to output directory for remaining steps
            os.chdir(self.output_dir)
            
            # Steps 3-8
            self.run_step3()
            self.run_step4()
            self.run_step5()
            self.run_step6()
            self.run_step7()
            self.run_step8()
            
            # Summary
            self._log("\n" + "="*60)
            self._log("Analysis completed successfully!")
            self._log("="*60)
            self._log(f"\nResults saved in: {self.output_dir}/")
            self._log("\nKey output files:")
            self._log("  - Core SNP alignment: *.bak.fa")
            self._log("  - Distance matrix: distance_matrix.txt")
            self._log("  - SNP results: *.snp files")
            
        finally:
            if self.log_f:
                self.log_f.close()
