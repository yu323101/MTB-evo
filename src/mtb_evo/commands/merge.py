"""Step 8: Merge FAS files into a single alignment."""

from pathlib import Path

import typer
from typer import Option


def merge_fas(fas_dir: Path, output: Path) -> None:
    """
    Merge all *.fas and *.fasta files into a single multi-sequence FASTA file.

    This function implements: cat *.fas *.fasta > all_strains.fa
    """
    # Find all FAS and FASTA files
    fas_files = sorted(fas_dir.glob("*.fas")) + sorted(fas_dir.glob("*.fasta"))
    if not fas_files:
        raise ValueError(f"No .fas or .fasta files found in {fas_dir}")

    typer.echo(f"Found {len(fas_files)} FAS/FASTA files")

    # Merge files
    with open(output, "w") as out_f:
        for fas_file in fas_files:
            with open(fas_file) as in_f:
                out_f.write(in_f.read())
                # Ensure file ends with newline
                if not in_f.read().endswith("\n"):
                    out_f.write("\n")

    typer.echo(f"Merged {len(fas_files)} files into {output}")


def merge_cmd(
    fas_dir: Path = Option(
        Path("."), "--fas-dir", "-f", help="Directory containing .fas or .fasta files"
    ),
    output: Path = Option(
        Path("all_strains.fa"), "--output", "-o", help="Output merged FASTA file"
    ),
) -> None:
    """Merge FAS files into a single alignment."""
    merge_fas(fas_dir, output)
    typer.echo(f"Merge completed: {output}")
