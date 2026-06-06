"""Filter SNP records against PPE and insertion-sequence loci."""

from pathlib import Path

import typer
from typer import Option


def ppe_filter(ppe_list: Path, input_file: Path, output_file: Path) -> None:
    """
    Filter PPE regions and insertion sequences.
    
    Args:
        ppe_list: Path to PPE_INS_loci.list file containing regions to filter
        input_file: Path to SNP list file (vars)
        output_file: Path to output filtered file (var.ppe)
    
    Logic:
        1. Read PPE/IS regions into a set for O(1) lookup
        2. Read SNP list and check if position is in PPE/IS regions
        3. Output SNPs that are NOT in PPE/IS regions
    """
    # Read PPE/IS regions into a set
    ppe_regions = set()
    with open(ppe_list, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                ppe_regions.add(line)
    
    typer.echo(f"  Loaded {len(ppe_regions)} PPE/IS regions")
    
    # Filter SNPs
    filtered_count = 0
    total_count = 0
    
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            total_count += 1
            line = line.strip()
            
            # Split by tab
            cols = line.split('\t')
            if len(cols) < 2:
                continue
            
            # Check if position is in PPE/IS regions
            position = cols[1]
            if position not in ppe_regions:
                f_out.write(line + '\n')
                filtered_count += 1
    
    typer.echo(f"  Processed {total_count} SNPs, retained {filtered_count}")


def ppe_filter_cmd(
    ppe_list: Path = Option(..., "--ppe-list", "-p", help="PPE/IS regions list file"),
    input_file: Path = Option(..., "--input", "-i", help="Input SNP list file (.vars)"),
    output_file: Path = Option(..., "--output", "-o", help="Output filtered file (.var.ppe)"),
) -> None:
    """Filter PPE regions and insertion sequences (replaces 0.1_PE_IS_filt_Rv.pl)."""
    ppe_filter(ppe_list, input_file, output_file)
    typer.echo(f"PPE/IS filtering completed: {output_file}")
