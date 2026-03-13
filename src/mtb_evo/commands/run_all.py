"""Step 1-8: Run complete MTB-Evo pipeline."""

import subprocess
import sys
import time
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


def run_step1(samples: Path, output_dir: Path, threads: int, sort_threads: int):
    """Step 1: Generate SNP calling script."""
    typer.echo("[1/8] Step 1: Generating SNP calling script...")
    
    # Check tools
    missing = check_tools()
    if missing:
        typer.echo(f"❌ Missing tools: {', '.join(missing)}")
        typer.echo("Please activate conda environment: conda activate mtb-evo")
        sys.exit(1)
    
    # Get absolute paths
    script_dir = Path(__file__).parent.parent.parent.parent  # mtb-evo root directory
    pair_script = script_dir / "scripts" / "pair_fixed_nostrandbias.py"
    samples_abs = samples.absolute()
    
    # Verify script exists
    if not pair_script.exists():
        typer.echo(f"❌ Script not found: {pair_script}")
        sys.exit(1)
    
    # Verify samples file exists
    if not samples_abs.exists():
        typer.echo(f"❌ Sample list not found: {samples_abs}")
        sys.exit(1)
    
    typer.echo(f"  📄 Using script: {pair_script}")
    typer.echo(f"  📄 Using samples: {samples_abs}")
    
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
        subprocess.run(cmd, check=True, capture_output=True)
        typer.echo("  ✓ Generated: results/pair_end.sh")
        typer.echo("  ✓ Tools detected: sickle, bowtie2, samtools, java, VarScan")
        
        # Count strains
        with open(samples) as f:
            strain_count = len([line for line in f if line.strip()])
        typer.echo(f"  ✓ Found {strain_count} strains to process")
        
    except subprocess.CalledProcessError as e:
        typer.echo(f"❌ Failed to generate script: {e}")
        sys.exit(1)


def run_step2(output_dir: Path):
    """Step 2: Run SNP calling in background."""
    typer.echo("\n[2/8] Step 2: Running SNP calling (background)")
    
    script_path = output_dir / "pair_end.sh"
    log_path = output_dir / "pair_end.log"
    
    if not script_path.exists():
        typer.echo(f"❌ Script not found: {script_path}")
        typer.echo("Please run Step 1 first.")
        sys.exit(1)
    
    # Check if already running
    result = subprocess.run(
        ["pgrep", "-f", "pair_end.sh"],
        capture_output=True
    )
    
    if result.returncode == 0:
        typer.echo("  ⚠️  SNP calling is already running")
    else:
        # Start in background
        with open(log_path, "w") as log_f:
            subprocess.Popen(
                ["bash", str(script_path)],
                stdout=log_f,
                stderr=subprocess.STDOUT,
                cwd=output_dir
            )
        typer.echo(f"  ✓ Started: {script_path}")
    
    typer.echo(f"  📄 Log file: {log_path}")
    typer.echo("  ⏱️  This step may take 2-4 hours.")
    typer.echo("  💡 Use 'tail -f results/pair_end.log' to monitor progress.")
    typer.echo("\n  📝 Next steps (3-8) will run automatically after Step 2 completes.")


def check_step2_complete(output_dir: Path, expected_count: int) -> bool:
    """Check if Step 2 is complete by counting .snp files."""
    snp_files = list(output_dir.glob("*.snp"))
    return len(snp_files) >= expected_count


def run_all(
    samples: Path = Option(..., "--samples", "-s", help="Sample list file"),
    output_dir: Path = Option(Path("results"), "--output-dir", "-o", help="Output directory"),
    threads: int = Option(None, "--threads", "-t", help="Number of threads for bowtie2"),
    sort_threads: int = Option(None, "--sort-threads", help="Number of threads for samtools sort"),
    wait: bool = Option(False, "--wait", "-w", help="Wait for Step 2 to complete"),
) -> None:
    """Run complete MTB-Evo pipeline (Steps 1-8)."""
    
    # Validate inputs
    if not samples.exists():
        typer.echo(f"❌ Sample list not found: {samples}")
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Count expected samples
    with open(samples) as f:
        expected_samples = len([line for line in f if line.strip()])
    
    # Step 1: Generate script
    run_step1(samples, output_dir, threads, sort_threads)
    
    # Step 2: Run SNP calling
    run_step2(output_dir)
    
    if wait:
        # Wait for Step 2 to complete
        typer.echo("\n⏳ Waiting for Step 2 to complete...")
        while not check_step2_complete(output_dir, expected_samples):
            time.sleep(30)
        typer.echo("  ✓ Step 2 completed!")
    else:
        # Check if already complete
        if not check_step2_complete(output_dir, expected_samples):
            typer.echo("\n⚠️  Step 2 is still running.")
            typer.echo("   Please wait for it to complete, then re-run this command.")
            sys.exit(0)
    
    # Import commands for Steps 3-8
    from mtb_evo.commands.diff_loci import diff_loci_cmd
    from mtb_evo.commands.recall import recall_cmd
    from mtb_evo.commands.merge import merge_cmd
    from mtb_evo.commands.wild_extract import wild_extract_cmd
    from mtb_evo.commands.filter import filter_cmd
    from mtb_evo.commands.distance import distance_cmd
    
    # Change to output directory
    import os
    os.chdir(output_dir)
    
    # Step 3: Extract differential loci
    typer.echo("\n[3/8] Step 3: Extracting differential loci...")
    diff_loci_cmd(Path("."), Path("diff_loci.txt"))
    
    # Step 4: Recall genotypes for all samples
    typer.echo("\n[4/8] Step 4: Recalling genotypes...")
    cns_files = list(Path(".").glob("*.cns"))
    for cns_file in cns_files:
        output_name = cns_file.stem.replace(".cns", "") + ".recall.fasta"
        recall_cmd(
            Path("diff_loci.txt"),
            None,  # Use default depth
            cns_file,
            Path(output_name)
        )
    
    # Step 5: Merge sequences
    typer.echo("\n[5/8] Step 5: Merging sequences...")
    merge_cmd(Path("."), Path("merged.fasta"))
    
    # Step 6: Extract wild-type bases
    typer.echo("\n[6/8] Step 6: Extracting wild-type bases...")
    ancestor = Path("../data/tb.ancestor.fasta")
    if not ancestor.exists():
        ancestor = Path("data/tb.ancestor.fasta")
    wild_extract_cmd(Path("diff_loci.txt"), ancestor, Path("wildtype.fasta"))
    
    # Step 7: Filter core SNPs
    typer.echo("\n[7/8] Step 7: Filtering core SNPs...")
    filter_cmd(Path("wildtype.fasta"), Path("merged.fasta"), 5, "core_snps")
    
    # Step 8: Calculate distances
    typer.echo("\n[8/8] Step 8: Calculating pairwise distances...")
    # Find the filtered alignment file
    bak_files = list(Path(".").glob("*.bak.fa"))
    if bak_files:
        distance_cmd(bak_files[0], Path("distance_matrix.txt"))
    else:
        typer.echo("  ⚠️  No filtered alignment file found")
    
    # Summary
    typer.echo("\n" + "="*60)
    typer.echo("🎉 Analysis completed successfully!")
    typer.echo("="*60)
    typer.echo(f"\nResults saved in: {output_dir}/")
    typer.echo("\nKey output files:")
    typer.echo("  • Core SNP alignment: *.bak.fa")
    typer.echo("  • Distance matrix: distance_matrix.txt")
    typer.echo("  • SNP results: *.snp files")
    typer.echo("\nNext steps:")
    typer.echo("  • View distance matrix: cat results/distance_matrix.txt")
    typer.echo("  • Build phylogenetic tree: use *.bak.fa file")


def run_all_cmd(
    samples: Path = Option(..., "--samples", "-s", help="Sample list file"),
    output_dir: Path = Option(Path("results"), "--output-dir", "-o", help="Output directory"),
    threads: int = Option(None, "--threads", "-t", help="Number of threads for bowtie2"),
    sort_threads: int = Option(None, "--sort-threads", help="Number of threads for samtools sort"),
    wait: bool = Option(False, "--wait", "-w", help="Wait for Step 2 to complete"),
) -> None:
    """Run complete MTB-Evo pipeline (Steps 1-8)."""
    run_all(samples, output_dir, threads, sort_threads, wait)
