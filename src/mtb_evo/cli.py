"""Command-line interface for MTB-Evo."""

from pathlib import Path
from typing import Optional

import typer

from mtb_evo.commands.diff_loci import diff_loci_cmd
from mtb_evo.commands.recall import recall_cmd
from mtb_evo.commands.merge import merge_cmd
from mtb_evo.commands.wild_extract import wild_extract_cmd
from mtb_evo.commands.filter import filter_cmd
from mtb_evo.commands.distance import distance_cmd

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


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
