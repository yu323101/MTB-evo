"""Transform filtered VarScan output into the downstream text format."""

from pathlib import Path

import typer
from typer import Option


def format_transformation(input_file: Path, output_file: Path) -> None:
    """
    Transform VarScan output format.
    
    Original Perl logic:
    - Skip header line (starts with 'Chrom')
    - Split columns by tab
    - Split columns 5 and 6 by colon
    - Format output based on number of elements in column 6
    """
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            line = line.strip()
            
            # Skip header line
            if line.startswith('Chrom'):
                continue
            
            # Split by tab
            cols = line.split('\t')
            if len(cols) < 10:
                continue
            
            # Split columns 5 and 6 (index 4 and 5) by colon
            col5_parts = cols[4].split(':')
            col6_parts = cols[5].split(':')
            
            # Start building output
            output_parts = [
                cols[0],  # Chrom
                cols[1],  # Position
                cols[2],  # Ref
                cols[3],  # Var
                col5_parts[4] if len(col5_parts) > 4 else '',  # b[4]
                col5_parts[1] if len(col5_parts) > 1 else '',  # b[1]
            ]
            
            # Format based on number of elements in column 6
            if len(col6_parts) == 7:
                # Original: printf "%-15s\t","$b[2]=$c[2]:$c[3]";
                field1 = f"{col5_parts[2]}={col6_parts[2]}:{col6_parts[3]}"
                field2 = f"{col5_parts[3]}={col6_parts[4]}:{col6_parts[5]}"
                field3 = f"{col6_parts[0]}:{col6_parts[1]}={col6_parts[6]}"
                
                output_parts.extend([
                    f"{field1:<15}",
                    f"{field2:<15}",
                    f"{field3:<20}",
                    cols[6], cols[7], cols[8], cols[9]
                ])
                
            elif len(col6_parts) == 6:
                # Original: printf "%-15s\t","$b[2]=$c[1]:$c[2]";
                field1 = f"{col5_parts[2]}={col6_parts[1]}:{col6_parts[2]}"
                field2 = f"{col5_parts[3]}={col6_parts[3]}:{col6_parts[4]}"
                field3 = f"{col6_parts[0]}={col6_parts[5]}"
                
                output_parts.extend([
                    f"{field1:<15}",
                    f"{field2:<15}",
                    f"{field3:<20}",
                    cols[6], cols[7], cols[8], cols[9]
                ])
            
            # Write output
            f_out.write('\t'.join(output_parts) + '\n')


def format_trans_cmd(
    input_file: Path = Option(..., "--input", "-i", help="Input .var.ppe file"),
    output_file: Path = Option(..., "--output", "-o", help="Output .var.for file"),
) -> None:
    """Transform VarScan output format (replaces 1_format_trans.pl)."""
    format_transformation(input_file, output_file)
    typer.echo(f"Format transformation completed: {output_file}")
