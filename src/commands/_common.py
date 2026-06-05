"""Shared helpers for command wrappers."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer


def resolve_samples_input(samples: Optional[Path], samplesheet: Optional[Path]) -> Path:
    if not samples and not samplesheet:
        raise typer.BadParameter("Either --samples or --samplesheet must be provided")
    if samples and samplesheet:
        raise typer.BadParameter("Please provide only one of --samples or --samplesheet")

    input_file = samplesheet or samples
    if not input_file or not input_file.exists():
        raise typer.BadParameter(f"Input sample file not found: {input_file}")
    return input_file
