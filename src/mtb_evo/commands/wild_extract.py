"""Step 9: Extract wild-type bases from ancestor sequence."""

from pathlib import Path

import typer
from typer import Option


def extract_wild_loci(loci_file: Path, ancestor_fasta: Path, output: Path) -> None:
    """
    Extract wild-type bases at specified loci from ancestor sequence.

    This function implements the logic from 3rd_wild_extract.pl:
    1. Read loci list
    2. Read ancestor sequence (skip FASTA header)
    3. Extract base at each position (1-based coordinates)
    4. Output coordinate and base
    """
    # Read loci list
    loci = []
    with open(loci_file) as f:
        for line in f:
            line = line.strip()
            if line:
                loci.append(int(line))

    typer.echo(f"Read {len(loci)} loci from {loci_file}")

    # Read ancestor sequence
    seq = ""
    with open(ancestor_fasta) as f:
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                continue  # Skip FASTA header
            seq += line

    typer.echo(f"Read ancestor sequence: {len(seq)} bp")

    # Extract bases (1-based coordinates)
    extracted = 0
    with open(output, "w") as f:
        for pos in loci:
            if 1 <= pos <= len(seq):
                base = seq[pos - 1]  # Convert to 0-based
                f.write(f"{pos}\t{base}\n")
                extracted += 1
            else:
                f.write(f"{pos}\tN\n")  # Out of range

    typer.echo(f"Extracted {extracted} bases (out of range: {len(loci) - extracted})")


def wild_extract_cmd(
    loci: Path = Option(..., "--loci", "-l", help="Loci list file"),
    ancestor: Path = Option(..., "--ancestor", "-a", help="Ancestor FASTA file"),
    output: Path = Option(..., "--output", "-o", help="Output wild loci file"),
) -> None:
    """Extract wild-type bases from ancestor sequence."""
    extract_wild_loci(loci, ancestor, output)
    typer.echo(f"Wild-type bases extracted: {output}")
