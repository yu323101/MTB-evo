"""Prepare report input files from sample results and FASTQ inputs."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional

import typer
from typer import Option

from src.commands._common import resolve_samples_input
from src.core.report_inputs import (
    parse_samples_input,
    prepare_sample_downstream_inputs_from_results,
    prepare_sample_foundation_outputs,
)
from src.utils.logging_config import get_logger
from src.utils.tools import ToolManager


logger = get_logger("commands.prepare_downstream_inputs")


def _write_status(status_file: Path, rows: List[Dict[str, str]]) -> None:
    status_file.parent.mkdir(parents=True, exist_ok=True)
    with open(status_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["sample_id", "status", "issues", "run_id", "stage"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)


def _prepare_foundation(
    samples_file: Path,
    output_dir: Path,
    status_file: Path,
    run_id: str,
) -> Path:
    sample_rows = parse_samples_input(samples_file)
    samples_dir = output_dir / "samples"
    status_rows: List[Dict[str, str]] = []

    for row in sample_rows:
        sample_id = str(row["sample_id"])
        issues: List[str] = []
        r1 = Path(str(row["r1"]))
        r2 = Path(str(row["r2"]))
        if not r1.exists():
            issues.append(f"MISSING_R1:{r1}")
        if not r2.exists():
            issues.append(f"MISSING_R2:{r2}")

        if not issues:
            try:
                prepare_sample_foundation_outputs(
                    sample_id=sample_id,
                    r1=r1,
                    r2=r2,
                    sample_dir=samples_dir / sample_id,
                )
                logger.info("Foundation prepared: %s", sample_id)
            except Exception as e:
                issues.append(str(e))
                logger.error("Foundation failed: %s (%s)", sample_id, e)

        status_rows.append(
            {
                "sample_id": sample_id,
                "status": "OK" if not issues else "FAILED",
                "issues": ";".join(issues),
                "run_id": run_id,
                "stage": "foundation_prepare",
            }
        )

    _write_status(status_file, status_rows)
    failed = [r for r in status_rows if r["status"] != "OK"]
    if failed:
        raise typer.Exit(code=1)
    return status_file


def _prepare_downstream(
    samples_file: Path,
    output_dir: Path,
    samtools_path: Path,
    status_file: Path,
    run_id: str,
) -> Path:
    sample_rows = parse_samples_input(samples_file)
    samples_dir = output_dir / "samples"
    status_rows: List[Dict[str, str]] = []

    for row in sample_rows:
        sample_id = str(row["sample_id"])
        issues: List[str] = []
        try:
            prepare_sample_downstream_inputs_from_results(
                sample_id=sample_id,
                sample_dir=samples_dir / sample_id,
                samtools=samtools_path,
            )
            logger.info("Downstream prepared: %s", sample_id)
        except Exception as e:
            issues.append(str(e))
            logger.error("Downstream prepare failed: %s (%s)", sample_id, e)

        status_rows.append(
            {
                "sample_id": sample_id,
                "status": "OK" if not issues else "FAILED",
                "issues": ";".join(issues),
                "run_id": run_id,
                "stage": "downstream_prepare",
            }
        )

    _write_status(status_file, status_rows)
    failed = [r for r in status_rows if r["status"] != "OK"]
    if failed:
        raise typer.Exit(code=1)
    return status_file


def prepare_downstream_inputs_cmd(
    samples: Optional[Path] = Option(None, "--samples", "-s", help="Legacy sample list file"),
    samplesheet: Optional[Path] = Option(
        None, "--samplesheet", help="CSV sample sheet with columns: sample_id,r1,r2"
    ),
    output_dir: Path = Option(Path("results"), "--output-dir", "-o", help="Output directory"),
    foundation_status_output: Optional[Path] = Option(
        None,
        "--foundation-status-output",
        help="Foundation status TSV output path",
    ),
    downstream_status_output: Optional[Path] = Option(
        None,
        "--downstream-status-output",
        help="Downstream status TSV output path",
    ),
    run_id: str = Option("", "--run-id", help="Run identifier stored in status metadata"),
    verbose: bool = Option(False, "--verbose", "-v", help="Enable verbose (debug) logging"),
    mode: str = Option("light", "--mode", help="Preparation mode: foundation, light, or full"),
) -> None:
    """Prepare B1/C inputs from existing sample outputs and FASTQ inputs."""

    if mode not in {"foundation", "light", "full"}:
        raise typer.BadParameter("--mode must be one of: foundation, light, full")

    input_file = resolve_samples_input(samples, samplesheet)
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    foundation_status_file = (
        foundation_status_output.resolve()
        if foundation_status_output is not None
        else output_dir / "logs" / "prepare_foundation_outputs_status.tsv"
    )
    downstream_status_file = (
        downstream_status_output.resolve()
        if downstream_status_output is not None
        else output_dir / "logs" / "prepare_downstream_inputs_status.tsv"
    )

    logger.info(
        "Starting prepare-downstream-inputs with input=%s output_dir=%s mode=%s",
        input_file,
        output_dir,
        mode,
    )

    tools = ToolManager()
    if mode in {"foundation", "full"} and not tools.is_available("fastp"):
        logger.error("Missing required tool: fastp")
        raise typer.Exit(code=1)
    if mode in {"light", "full"} and not tools.is_available("samtools"):
        logger.error("Missing required tool: samtools")
        raise typer.Exit(code=1)

    if mode in {"foundation", "full"}:
        _prepare_foundation(
            input_file,
            output_dir,
            foundation_status_file,
            run_id=run_id,
        )
    if mode in {"light", "full"}:
        samtools_path = tools.get_path("samtools")
        _prepare_downstream(
            input_file,
            output_dir,
            samtools_path,
            downstream_status_file,
            run_id=run_id,
        )

    if verbose:
        logger.debug("prepare-downstream-inputs completed successfully")
    logger.info("Completed prepare-downstream-inputs mode=%s output_dir=%s", mode, output_dir)
