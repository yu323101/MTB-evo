"""Build report outputs from pipeline results."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import typer
from typer import Option

from src.commands._common import resolve_samples_input
from src.commands.lineage import run_lineage
from src.commands.report_figures import run_report_figures
from src.commands.report_tables import run_report_tables
from src.utils.logging_config import get_logger

logger = get_logger("commands.build_reports")
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_step(
    name: str,
    strict: bool,
    fn: Callable[[], None],
) -> tuple[bool, str]:
    try:
        fn()
        logger.info("%s completed", name)
        return True, ""
    except Exception as e:
        logger.error("%s failed: %s", name, e)
        if strict:
            raise typer.Exit(code=1) from e
        return False, str(e)


def build_reports_cmd(
    samples: Optional[Path] = Option(None, "--samples", "-s", help="Legacy sample list file"),
    samplesheet: Optional[Path] = Option(
        None, "--samplesheet", help="CSV sample sheet with columns: sample_id,r1,r2"
    ),
    output_dir: Path = Option(Path("results"), "--output-dir", "-o", help="Output directory"),
    lineage_summary_output: Path = Option(
        Path("results/logs/lineage_summary.tsv"),
        "--lineage-summary-output",
        help="Lineage summary TSV output",
    ),
    figure_status_output: Path = Option(
        Path("results/logs/report_figures_status.tsv"),
        "--figure-status-output",
        help="Figure status TSV output",
    ),
    table_status_output: Path = Option(
        Path("results/logs/report_tables_status.tsv"),
        "--table-status-output",
        help="Table status TSV output",
    ),
    run_id: str = Option("", "--run-id", help="Run identifier stored in status metadata"),
    verbose: bool = Option(False, "--verbose", "-v", help="Enable verbose (debug) logging"),
    skip_lineage: bool = Option(False, "--skip-lineage", help="Skip lineage assignment"),
    skip_figures: bool = Option(False, "--skip-figures", help="Skip figure reporting"),
    skip_tables: bool = Option(False, "--skip-tables", help="Skip table reporting"),
    strict: bool = Option(False, "--strict", help="Fail if any report step fails"),
) -> None:
    """Build lineage, figure, and table outputs from standardized results layout."""

    input_file = resolve_samples_input(samples, samplesheet)
    output_dir = output_dir.resolve()
    samples_dir = output_dir / "samples"
    lineage_summary_output = lineage_summary_output.resolve()
    figure_status_output = figure_status_output.resolve()
    table_status_output = table_status_output.resolve()
    lineage_summary_output.parent.mkdir(parents=True, exist_ok=True)
    figure_status_output.parent.mkdir(parents=True, exist_ok=True)
    table_status_output.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Starting build-reports with input=%s output_dir=%s", input_file, output_dir)
    if verbose:
        logger.debug("Verbose mode enabled for build-reports")

    failures: list[str] = []

    if skip_lineage:
        logger.info("Skipping lineage assignment (--skip-lineage)")
    else:
        ok, err = _run_step(
            "lineage",
            strict,
            lambda: run_lineage(
                output_dir,
                PROJECT_ROOT / "data" / "lineage" / "typing_SNP.tsv",
                lineage_summary_output,
                run_id=run_id,
                stage="lineage",
            ),
        )
        if not ok:
            failures.append(f"lineage:{err}")

    if skip_figures:
        logger.info("Skipping figure reporting (--skip-figures)")
    else:
        ok, err = _run_step(
            "report-figures",
            strict,
            lambda: run_report_figures(
                output_dir,
                samples_dir,
                figure_status_output,
                run_id=run_id,
                stage="report_figures",
            ),
        )
        if not ok:
            failures.append(f"report-figures:{err}")

    if skip_tables:
        logger.info("Skipping table reporting (--skip-tables)")
    else:
        ok, err = _run_step(
            "report-tables",
            strict,
            lambda: run_report_tables(
                output_dir,
                samples_dir,
                table_status_output,
                pipeline_version="v1",
                run_id=run_id,
                stage="report_tables",
            ),
        )
        if not ok:
            failures.append(f"report-tables:{err}")

    if failures:
        logger.warning("build-reports completed with failures (strict=%s): %s", strict, "; ".join(failures))
    else:
        logger.info("Completed build-reports for output_dir=%s", output_dir)
