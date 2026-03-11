"""Step 4: Extract differential loci from SNP files."""

from collections import defaultdict
from pathlib import Path

import typer
from typer import Option


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
    snp_files = list(snp_dir.glob("*.snp"))
    if not snp_files:
        raise ValueError(f"No .snp files found in {snp_dir}")

    total_samples = len(snp_files)
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

    typer.echo(f"Total unique loci: {len(locus_count)}")
    typer.echo(f"Differential loci: {len(diff_loci)}")

    # Sort and output
    with open(output, "w") as f:
        for pos in sorted(diff_loci):
            f.write(f"{pos}\n")


def diff_loci_cmd(
    snp_dir: Path = Option(
        Path("."), "--snp-dir", "-s", help="Directory containing .snp files"
    ),
    output: Path = Option(
        Path("diff_location.list"), "--output", "-o", help="Output loci list file"
    ),
) -> None:
    """Extract differential loci from SNP files."""
    extract_diff_loci(snp_dir, output)
    typer.echo(f"Differential loci extracted: {output}")
