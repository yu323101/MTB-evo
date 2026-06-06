"""Extract differential loci from SNP files."""

from collections import defaultdict
from pathlib import Path

import typer
from typer import Option

from src.utils.logging_config import get_logger


logger = get_logger("commands.diff_loci")


def discover_snp_files(snp_dir: Path) -> list[Path]:
    candidates = []
    candidates.extend(sorted(snp_dir.glob("*.snp")))
    candidates.extend(sorted((snp_dir / "samples").glob("*/variant_analysis/*.snp")))
    candidates.extend(sorted(snp_dir.glob("*/variant_analysis/*.snp")))

    seen = set()
    snp_files = []
    for path in candidates:
        resolved = str(path.resolve())
        if resolved in seen:
            continue
        seen.add(resolved)
        snp_files.append(path)
    return snp_files


def extract_diff_loci(snp_dir: Path, output: Path) -> None:
    """
    Extract differential loci (not present in all samples) from SNP files.

    This function implements the logic from 1_diff_location_extract.pl:
    1. Find all *.snp files in directory
    2. Count occurrence of each locus across samples
    3. Keep only loci that appear in < total_samples (not conserved)
    4. Sort and output
    """
    # Find all SNP files
    logger.info("Extracting differential loci from %s to %s", snp_dir, output)
    snp_files = discover_snp_files(snp_dir)
    if not snp_files:
        raise ValueError(f"No .snp files found in {snp_dir}")

    total_samples = len(snp_files)
    logger.info("Found %d SNP files", total_samples)
    typer.echo(f"Found {total_samples} SNP files")

    # Count locus occurrence
    locus_count = defaultdict(int)

    for snp_file in snp_files:
        seen_in_this_sample = set()
        with open(snp_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                cols = line.split()
                if len(cols) >= 1:
                    try:
                        pos = int(cols[0])
                        if pos not in seen_in_this_sample:
                            locus_count[pos] += 1
                            seen_in_this_sample.add(pos)
                    except ValueError:
                        continue

    # Filter differential loci (not in all samples)
    diff_loci = [pos for pos, count in locus_count.items() if count < total_samples]

    logger.info("Total unique loci: %d", len(locus_count))
    logger.info("Differential loci retained: %d", len(diff_loci))
    typer.echo(f"Total unique loci: {len(locus_count)}")
    typer.echo(f"Differential loci: {len(diff_loci)}")

    # Sort and output
    with open(output, "w") as f:
        for pos in sorted(diff_loci):
            f.write(f"{pos}\n")


def diff_loci_cmd(
    snp_dir: Path = Option(
        Path("."), "--snp-dir", "-s", help="Directory containing .snp files or samples/ layout"
    ),
    output: Path = Option(
        Path("diff_location.list"), "--output", "-o", help="Output loci list file"
    ),
) -> None:
    """Extract differential loci from SNP files."""
    extract_diff_loci(snp_dir, output)
    logger.info("Differential loci extracted: %s", output)
    typer.echo(f"Differential loci extracted: {output}")
