"""Command-line interface for MTB-Evo."""

from pathlib import Path
from typing import Optional

import typer

from src.commands.diff_loci import diff_loci_cmd
from src.commands.recall import recall_cmd
from src.commands.merge import merge_cmd
from src.commands.wild_extract import wild_extract_cmd
from src.commands.filter import filter_cmd
from src.commands.distance import distance_cmd
from src.commands.run_all import run_all_cmd
from src.commands.format_trans import format_trans_cmd
from src.commands.ppe_filter import ppe_filter_cmd
from src.commands.filter_fasta import filter_fasta_cmd

app = typer.Typer(
    name="mtb-evo",
    help="Mycobacterium tuberculosis evolutionary analysis pipeline",
    no_args_is_help=True,
)

# Register commands
app.command("diff-loci")(diff_loci_cmd)
app.command("recall")(recall_cmd)
app.command("merge")(merge_cmd)
app.command("wild-extract")(wild_extract_cmd)
app.command("filter")(filter_cmd)
app.command("distance")(distance_cmd)
app.command("run-all")(run_all_cmd)
app.command("format-trans")(format_trans_cmd)
app.command("ppe-filter")(ppe_filter_cmd)
app.command("filter-fasta")(filter_fasta_cmd)


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
