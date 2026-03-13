"""Step 1-8: Run complete MTB-Evo pipeline with logging to file."""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import typer
from typer import Option


def check_tools():
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


def run_step1(samples: Path, output_dir: Path, threads: int, sort_threads: int, log_f):
    """Step 1: Generate SNP calling script."""
    log_f.write("[1/8] Step 1: Generating SNP calling script...\n")
    
    # Check tools
    missing = check_tools()
    if missing:
        log_f.write(f"❌ Missing tools: {', '.join(missing)}\n")
        log_f.write("Please activate conda environment: conda activate mtb-evo\n")
        sys.exit(1)
    
    # Get absolute paths
    script_dir = Path(__file__).parent.parent.parent.parent
    pair_script = script_dir / "scripts" / "pair_fixed_nostrandbias.py"
    samples_abs = samples.absolute()
    
    # Verify script exists
    if not pair_script.exists():
        log_f.write(f"❌ Script not found: {pair_script}\n")
        sys.exit(1)
    
    # Verify samples file exists
    if not samples_abs.exists():
        log_f.write(f"❌ Sample list not found: {samples_abs}\n")
        sys.exit(1)
    
    log_f.write(f"  📄 Using script: {pair_script}\n")
    log_f.write(f"  📄 Using samples: {samples_abs}\n")
    
    # Generate script
    cmd = [
        "python3", 
        str(pair_script),
        str(samples_abs),
    ]
    
    if threads:
        cmd.extend(["--threads", str(threads)])
    if sort_threads:
        cmd.extend(["--sort-threads", str(sort_threads)])
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
            cwd=script_dir
        )
        
        stdout, stderr = process.communicate(input='y\n', timeout=600)
        
        if process.returncode != 0:
            log_f.write(f"❌ Script failed with error:\n")
            log_f.write(stderr)
            sys.exit(1)
        
        if stdout:
            for line in stdout.split('\n'):
                if line.strip():
                    log_f.write(f"    {line}\n")
        
        log_f.write("  ✓ Generated: results/pair_end.sh\n")
        log_f.write("  ✓ Tools detected: sickle, bowtie2, samtools, java, VarScan\n")
        
        with open(samples) as f:
            strain_count = len([line for line in f if line.strip()])
        log_f.write(f"  ✓ Found {strain_count} strains to process\n")
        
    except subprocess.TimeoutExpired:
        log_f.write("❌ Timeout: Script took too long (>10 minutes)\n")
        process.kill()
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        log_f.write(f"❌ Failed to generate script: {e}\n")
        sys.exit(1)


def run_step2(output_dir: Path, script_dir: Path, log_f):
    """Step 2: Run SNP calling in background."""
    log_f.write("\n[2/8] Step 2: Running SNP calling (background)\n")
    
    script_path = output_dir / "pair_end.sh"
    log_path = output_dir / "pair_end.log"
    
    if not script_path.exists():
        log_f.write(f"❌ Script not found: {script_path}\n")
        log_f.write("Please run Step 1 first.\n")
        sys.exit(1)
    
    result = subprocess.run(
        ["pgrep", "-f", "pair_end.sh"],
        capture_output=True
    )
    
    if result.returncode == 0:
        log_f.write("  ⚠️  SNP calling is already running\n")
    else:
        with open(log_path, "w") as log_file:
            subprocess.Popen(
                ["bash", str(script_path)],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=script_dir
            )
        log_f.write(f"  ✓ Started: {script_path}\n")
    
    log_f.write(f"  📄 Log file: {log_path}\n")
    log_f.write("  ⏱️  This step may take 2-4 hours.\n")
    log_f.write("  💡 Use 'tail -f results/pair_end.log' to monitor progress.\n")


def check_step2_complete(output_dir: Path, expected_count: int) -> bool:
    """Check if Step 2 is complete by counting .snp files."""
    snp_files = list(output_dir.glob("*.snp"))
    return len(snp_files) >= expected_count


def run_all(
    samples: Path = Option(..., "--samples", "-s", help="Sample list file"),
    output_dir: Path = Option(Path("results"), "--output-dir", "-o", help="Output directory"),
    threads: int = Option(None, "--threads", "-t", help="Number of threads for bowtie2"),
    sort_threads: int = Option(None, "--sort-threads", help="Number of threads for samtools sort"),
    foreground: bool = Option(False, "--foreground", "-f", help="Run in foreground and wait for completion"),
    log_file: Path = Option(None, "--log-file", "-l", help="Log file path (default: auto-generate)"),
) -> None:
    """Run complete MTB-Evo pipeline (Steps 1-8)."""
    
    # Validate inputs
    if not samples.exists():
        print(f"❌ Sample list not found: {samples}", file=sys.stderr)
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up log file
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = output_dir / f"run_all_{timestamp}.log"
    
    # Open log file
    log_f = open(log_file, 'w')
    
    try:
        # Print only log file path to terminal
        print(f"Log: {log_file}")
        
        # Get script directory
        script_dir = Path(__file__).parent.parent.parent.parent
        
        # Count expected samples
        with open(samples) as f:
            expected_samples = len([line for line in f if line.strip()])
        
        # Step 1: Generate script
        run_step1(samples, output_dir, threads, sort_threads, log_f)
        
        # Step 2: Run SNP calling
        run_step2(output_dir, script_dir, log_f)
        
        # Wait for Step 2 to complete
        if not check_step2_complete(output_dir, expected_samples):
            if foreground:
                log_f.write("\n⏳ Waiting for Step 2 to complete...\n")
                log_f.write(f"   Use 'tail -f {output_dir}/pair_end.log' to monitor progress\n")
                while not check_step2_complete(output_dir, expected_samples):
                    time.sleep(30)
                log_f.write("  ✓ Step 2 completed!\n")
            else:
                log_f.write("\n⏳ Monitoring Step 2 progress...\n")
                log_f.write("   This may take 2-4 hours. You can close this terminal.\n")
                log_f.write(f"   Use 'tail -f {output_dir}/pair_end.log' to check progress.\n")
                
                start_time = time.time()
                last_count = 0
                
                while not check_step2_complete(output_dir, expected_samples):
                    snp_files = list(output_dir.glob("*.snp"))
                    current_count = len(snp_files)
                    
                    if current_count > last_count:
                        elapsed = (time.time() - start_time) / 60
                        log_f.write(f"   Progress: {current_count}/{expected_samples} samples completed ({elapsed:.1f} min)\n")
                        log_f.flush()
                        last_count = current_count
                    
                    time.sleep(60)
                
                elapsed = (time.time() - start_time) / 60
                log_f.write(f"  ✓ Step 2 completed! ({elapsed:.1f} min)\n")
                log_f.write("  Continuing with Steps 3-8...\n")
        
        # Import commands for Steps 3-8
        from mtb_evo.commands.diff_loci import diff_loci_cmd
        from mtb_evo.commands.recall import recall_cmd
        from mtb_evo.commands.merge import merge_cmd
        from mtb_evo.commands.wild_extract import wild_extract_cmd
        from mtb_evo.commands.filter import filter_cmd
        from mtb_evo.commands.distance import distance_cmd
        
        import os
        os.chdir(output_dir)
        
        # Step 3: Extract differential loci
        log_f.write("\n[3/8] Step 3: Extracting differential loci...\n")
        log_f.flush()
        diff_loci_cmd(Path("."), Path("diff_loci.txt"))
        
        # Step 4: Recall genotypes
        log_f.write("\n[4/8] Step 4: Recalling genotypes...\n")
        log_f.flush()
        cns_files = list(Path(".").glob("*.cns"))
        for cns_file in cns_files:
            output_name = cns_file.stem.replace(".cns", "") + ".recall.fasta"
            recall_cmd(
                Path("diff_loci.txt"),
                None,
                cns_file,
                Path(output_name)
            )
        
        # Step 5: Merge sequences
        log_f.write("\n[5/8] Step 5: Merging sequences...\n")
        log_f.flush()
        merge_cmd(Path("."), Path("merged.fasta"))
        
        # Step 6: Extract wild-type bases
        log_f.write("\n[6/8] Step 6: Extracting wild-type bases...\n")
        log_f.flush()
        ancestor = Path("../data/tb.ancestor.fasta")
        if not ancestor.exists():
            ancestor = Path("data/tb.ancestor.fasta")
        wild_extract_cmd(Path("diff_loci.txt"), ancestor, Path("wildtype.fasta"))
        
        # Step 7: Filter core SNPs
        log_f.write("\n[7/8] Step 7: Filtering core SNPs...\n")
        log_f.flush()
        filter_cmd(Path("wildtype.fasta"), Path("merged.fasta"), 5, "core_snps")
        
        # Step 8: Calculate distances
        log_f.write("\n[8/8] Step 8: Calculating pairwise distances...\n")
        log_f.flush()
        bak_files = list(Path(".").glob("*.bak.fa"))
        if bak_files:
            distance_cmd(bak_files[0], Path("distance_matrix.txt"))
        else:
            log_f.write("  ⚠️  No filtered alignment file found\n")
        
        # Summary
        log_f.write("\n" + "="*60 + "\n")
        log_f.write("🎉 Analysis completed successfully!\n")
        log_f.write("="*60 + "\n")
        log_f.write(f"\nResults saved in: {output_dir}/\n")
        log_f.write("\nKey output files:\n")
        log_f.write("  • Core SNP alignment: *.bak.fa\n")
        log_f.write("  • Distance matrix: distance_matrix.txt\n")
        log_f.write("  • SNP results: *.snp files\n")
        
    finally:
        log_f.close()


def run_all_cmd(
    samples: Path = Option(..., "--samples", "-s", help="Sample list file"),
    output_dir: Path = Option(Path("results"), "--output-dir", "-o", help="Output directory"),
    threads: int = Option(None, "--threads", "-t", help="Number of threads for bowtie2"),
    sort_threads: int = Option(None, "--sort-threads", help="Number of threads for samtools sort"),
    foreground: bool = Option(False, "--foreground", "-f", help="Run in foreground and wait for completion"),
    log_file: Path = Option(None, "--log-file", "-l", help="Log file path (default: auto-generate)"),
) -> None:
    """Run complete MTB-Evo pipeline (Steps 1-8)."""
    run_all(samples, output_dir, threads, sort_threads, foreground, log_file)
