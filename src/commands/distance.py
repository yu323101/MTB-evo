"""Step 8: Calculate pairwise SNP distances."""

from pathlib import Path

import typer
from typer import Option

from src.utils.logging_config import get_logger


logger = get_logger("commands.distance")


def calculate_distance(
    alignment_file: Path,
    output: Path,
) -> None:
    """
    Calculate pairwise SNP distances from alignment.

    This function implements the logic from pair_distance_new.py:
    1. Parse FASTA alignment
    2. Compare all pairs of sequences
    3. Count differences (only A/C/G/T, skip N/?)
    4. Output distance matrix
    """
    # Step 1: Parse FASTA alignment
    logger.info("Calculating pairwise distance from %s to %s", alignment_file, output)
    sequences = {}
    names = []

    with open(alignment_file) as f:
        current_name = None
        current_seq = []

        for line in f:
            line = line.strip()
            if line.startswith(">"):
                if current_name:
                    sequences[current_name] = "".join(current_seq)
                current_name = line[1:]  # Remove ">"
                names.append(current_name)
                current_seq = []
            elif line:
                current_seq.append(line)

        if current_name:
            sequences[current_name] = "".join(current_seq)

    # Step 2: Calculate pairwise distances
    valid_bases = set("ACGT")

    with open(output, "w") as f:
        for i, name1 in enumerate(names):
            seq1 = sequences[name1]
            for j, name2 in enumerate(names):
                if i >= j:
                    continue  # Only calculate upper triangle

                seq2 = sequences[name2]
                dist = 0

                for a, b in zip(seq1, seq2):
                    if a not in valid_bases or b not in valid_bases:
                        continue  # Skip N/?
                    if a != b:
                        dist += 1

                f.write(f"{name1}\t{name2}\t{dist}\n")


def distance_cmd(
    alignment: Path = Option(..., "--alignment", "-a", help="Alignment FASTA file"),
    output: Path = Option(..., "--output", "-o", help="Output distance file"),
) -> None:
    """Calculate pairwise SNP distances."""
    calculate_distance(alignment, output)
    logger.info("Distance calculation completed: %s", output)
    typer.echo(f"Distance calculation completed: {output}")
