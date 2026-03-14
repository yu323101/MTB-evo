"""Step 1-8: Run complete MTB-Evo pipeline in daemon mode."""

import sys
from pathlib import Path

import typer
from typer import Option

from src.core.pipeline import MTBPipeline


def run_all_cmd(
    samples: Path = Option(..., "--samples", "-s", help="Sample list file"),
    output_dir: Path = Option(Path("results"), "--output-dir", "-o", help="Output directory"),
    threads: int = Option(None, "--threads", "-t", help="Number of threads for bowtie2"),
    sort_threads: int = Option(None, "--sort-threads", help="Number of threads for samtools sort"),
    verbose: bool = Option(False, "--verbose", "-v", help="Enable verbose (debug) logging"),
) -> None:
    """Run complete MTB-Evo pipeline (Steps 1-8) in daemon mode."""
    
    # Validate inputs
    if not samples.exists():
        print(f"Sample list not found: {samples}", file=sys.stderr)
        sys.exit(1)
    
    # Create pipeline instance with verbose parameter
    pipeline = MTBPipeline(
        samples=samples,
        output_dir=output_dir,
        threads=threads or 4,
        sort_threads=sort_threads or 2,
        verbose=verbose
    )
    
    # Daemonize and run
    pipeline.daemonize()
    pipeline.run_all()
