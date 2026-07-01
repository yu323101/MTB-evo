"""Recall genotypes from CNS files."""

from pathlib import Path
from typing import Dict, List, Optional, Set

import typer
from typer import Option


def recall_genotype(
    loci_file: Path,
    depth_file: Optional[Path],
    cns_file: Path,
    output: Path,
    default_depth: int = 10,
) -> None:
    """
    Back-calculate genotypes from CNS files based on differential loci.

    This function implements the logic from 1st_loci_recall_cns.pl:
    1. Read differential loci list
    2. Read depth threshold (or use default value 10)
    3. Parse CNS file and determine genotype for each locus
    4. Output FASTA format sequence
    """
    # Step 1: Read differential loci list
    loci: List[int] = []
    loci_set: Set[int] = set()
    genotype: Dict[int, str] = {}

    with open(loci_file) as f:
        for line in f:
            pos = int(line.strip())
            loci.append(pos)
            loci_set.add(pos)
            genotype[pos] = "N"  # Default to N

    # Step 2: Read depth threshold (10% of average depth)
    # If depth_file is provided and exists, use it; otherwise use default
    if depth_file and depth_file.exists():
        with open(depth_file) as f:
            avg_depth = int(f.read().strip())
    else:
        avg_depth = default_depth
    depth_threshold = avg_depth * 0.1

    # Step 3: Parse CNS file
    with open(cns_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("Chrom"):
                continue  # Skip header

            cols = line.split("\t")
            if len(cols) < 5:
                continue

            pos = int(cols[1])
            if pos not in loci_set:
                continue  # Only process differential loci

            ref = cols[2]
            var = cols[3]

            # Parse column 5: Cons:Cov:Reads1:Reads2:Freq:P-value
            info = cols[4].split(":")
            if len(info) < 6:
                genotype[pos] = "N"
                continue

            cons = info[0]
            cov_str = info[1]
            reads1_str = info[2]
            reads2_str = info[3]
            freq_str = info[4]

            # Filter 1: Only single base (filter indels)
            if len(var) != 1:
                genotype[pos] = "N"
                continue

            # Filter 2: Exclude failed calls (contains "-")
            if cov_str == "-" or reads1_str == "-" or reads2_str == "-":
                genotype[pos] = "N"
                continue

            # Filter 3: Depth threshold
            try:
                cov = int(cov_str)
            except ValueError:
                genotype[pos] = "N"
                continue

            if cov <= depth_threshold or cov < 3:
                genotype[pos] = "N"
                continue

            # Filter 4: Real reads ratio > 80%
            try:
                reads1 = int(reads1_str)
                reads2 = int(reads2_str)
                real_ratio = (reads1 + reads2) / cov
            except (ValueError, ZeroDivisionError):
                genotype[pos] = "N"
                continue

            if real_ratio <= 0.8:
                genotype[pos] = "N"
                continue

            # Filter 5-7: Frequency-based genotype determination
            try:
                # Remove % symbol if present and convert to int
                freq_clean = freq_str.rstrip('%')
                freq = int(float(freq_clean))
            except ValueError:
                genotype[pos] = "N"
                continue

            if freq >= 75:
                # Fixed mutation
                genotype[pos] = var if var != "." else cons
            elif freq <= 25:
                # Wild type
                genotype[pos] = ref
            else:
                # Mixed/unfixed (25% < freq < 75%)
                genotype[pos] = "?"

    # Step 4: Output FASTA format
    sample_name = cns_file.stem.replace(".cns", "").replace(".raw", "")
    with open(output, "w") as f:
        f.write(f">{sample_name}\n")
        for pos in loci:
            f.write(genotype[pos])
        f.write("\n")


def recall_cmd(
    loci: Path = Option(..., "--loci", "-l", help="Differential loci list file"),
    depth: Path = Option(None, "--depth", "-d", help="Depth threshold file (optional, default: 10)"),
    cns: Path = Option(..., "--cns", "-c", help="CNS file from VarScan"),
    output: Path = Option(..., "--output", "-o", help="Output FASTA file"),
) -> None:
    """Back-calculate genotypes from CNS files."""
    recall_genotype(loci, depth, cns, output)
    typer.echo(f"Genotype recall completed: {output}")
