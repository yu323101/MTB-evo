"""Generate report figures by orchestrating the original legacy scripts (01-09, PNG+PDF)."""

from __future__ import annotations

import csv
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import typer
from typer import Option

from src.core.report_inputs import annotated_variant_candidates
from src.reporting.variant_classification import write_normalized_annotated_from_cns
from src.utils.logging_config import get_logger

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEGACY_BASE = PROJECT_ROOT / "data" / "report_assets"
LEGACY_ALIAS = "N24_1"
logger = get_logger("commands.report_figures")


def _find_first(paths: List[Path]) -> Optional[Path]:
    for p in paths:
        if p.exists():
            return p
    return None


def _collect_samples(input_root: Path) -> List[str]:
    if input_root.name == "samples":
        candidates = sorted(input_root.glob("*/variant_analysis/*.cns"))
    else:
        candidates = sorted((input_root / "samples").glob("*/variant_analysis/*.cns"))

    if candidates:
        return sorted({p.stem for p in candidates})

    if input_root.name == "samples":
        snps = sorted(input_root.glob("*/variant_analysis/*.snp"))
    else:
        snps = sorted((input_root / "samples").glob("*/variant_analysis/*.snp"))
    if snps:
        return sorted({p.stem for p in snps})

    return []

def _sample_dir_name(sample_id: str) -> str:
    return sample_id if sample_id.endswith(".cleaned") else f"{sample_id}.cleaned"


def _sample_input_roots(input_root: Path, sample_id: str) -> List[Path]:
    names = [sample_id]
    canonical = _sample_dir_name(sample_id)
    if canonical != sample_id:
        names.append(canonical)

    roots: List[Path] = []
    for name in names:
        if input_root.name == "samples":
            roots.append(input_root / name)
        else:
            roots.append(input_root / "samples" / name)
    return roots


def _sample_output_dir(output_root: Path, sample_id: str) -> Path:
    name = _sample_dir_name(sample_id)
    return output_root / name if output_root.name == "samples" else output_root / "samples" / name


def _global_logs_dir(input_root: Path, output_root: Path) -> Path:
    if (input_root / "logs").exists():
        return input_root / "logs"
    if output_root.name == "samples":
        return output_root.parent / "logs"
    return output_root / "logs"



def _resolve_legacy_base(user_base: Optional[Path] = None) -> Path:
    candidates: List[Path] = []
    if user_base is not None:
        candidates.append(user_base)

    env_base = os.environ.get("MTB_EVO_REPORT_TEMPLATE_DIR")
    if env_base:
        candidates.append(Path(env_base))

    candidates.append(DEFAULT_LEGACY_BASE)

    for base in candidates:
        if (base / "scripts" / "generate_qc_figures.R").exists() and (
            base / "scripts" / "generate_variant_figures.R"
        ).exists():
            return base

    raise FileNotFoundError(
        f"Legacy figure scripts not found under {DEFAULT_LEGACY_BASE}. "
        "Set --legacy-base-dir or MTB_EVO_REPORT_TEMPLATE_DIR to override."
    )


def _safe_link_or_copy(src: Path, dst: Path) -> None:
    src = src.resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        if dst.exists() or dst.is_symlink():
            dst.unlink()
        os.symlink(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def _prepare_insert_sizes(input_root: Path, sample_id: str, work_dir: Path) -> Optional[Path]:
    sample_roots = _sample_input_roots(input_root, sample_id)
    candidates: List[Path] = []
    for root in sample_roots:
        candidates.extend(
            [
                root / "report_inputs" / "alignment_qc" / "insert_sizes.txt",
            ]
        )
    src = _find_first(candidates)
    if not src:
        return None

    out_file = work_dir / "qc_figures" / "insert_sizes.txt"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Keep only the first numeric column to satisfy generate_qc_figures.R input expectation.
    with open(src, "r", encoding="utf-8", errors="ignore") as fin, open(
        out_file, "w", encoding="utf-8"
    ) as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            first = line.split()[0]
            try:
                float(first)
            except ValueError:
                continue
            fout.write(f"{first}\n")

    return out_file


def _copy_figures(work_fig_dir: Path, out_fig_dir: Path, sample_id: str) -> int:
    out_fig_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for p in sorted(work_fig_dir.glob("*")):
        if p.suffix.lower() not in {".png", ".pdf"}:
            continue
        name = p.name.replace(f"_{LEGACY_ALIAS}_", f"_{sample_id}_")
        shutil.copy2(p, out_fig_dir / name)
        count += 1
    return count


def _prepare_sample_figure_dirs(sample_out: Path) -> Path:
    """Use `figure/` as the only canonical output dir."""
    canonical = sample_out / "figure"
    legacy = sample_out / "figures"

    if legacy.exists() and not canonical.exists() and not legacy.is_symlink():
        legacy.rename(canonical)
    canonical.mkdir(parents=True, exist_ok=True)
    if legacy.is_symlink():
        try:
            legacy.unlink()
        except OSError:
            pass
    return canonical


def run_report_figures(
    input_root: Path,
    output_root: Path,
    status_output: Path,
    legacy_base_dir: Optional[Path] = None,
    run_id: str = "",
    stage: str = "report_figures",
) -> Path:
    logger.info("Running report figures with input_root=%s output_root=%s", input_root, output_root)
    samples = _collect_samples(input_root)
    if not samples:
        raise ValueError(f"No sample inferred from {input_root} (*.cns/*.snp not found)")

    legacy_base = _resolve_legacy_base(legacy_base_dir)
    qc_script = legacy_base / "scripts" / "generate_qc_figures.R"
    var_script = legacy_base / "scripts" / "generate_variant_figures.R"

    status_rows: List[Dict[str, str]] = []
    logger.info("Discovered %d samples for figure generation", len(samples))

    for sample_id in samples:
        sample_out = _sample_output_dir(output_root, sample_id)
        fig_dir = _prepare_sample_figure_dirs(sample_out)
        log_dir = _global_logs_dir(input_root, output_root)
        fig_dir.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)
        sample_roots = _sample_input_roots(input_root, sample_id)

        fastp1 = _find_first(
            [root / "report_inputs" / "fastp_qc" / f"{sample_id}_1_fastp.json" for root in sample_roots]
        )
        fastp2 = _find_first(
            [root / "report_inputs" / "fastp_qc" / f"{sample_id}_2_fastp.json" for root in sample_roots]
        )
        depth = _find_first(
            [root / "report_inputs" / "alignment_qc" / f"{sample_id}.depth" for root in sample_roots]
        )
        cns = _find_first(
            [root / "variant_analysis" / f"{sample_id}.cns" for root in sample_roots]
        )
        annotated = _find_first(annotated_variant_candidates(sample_roots, sample_id))

        logger.info("Figure sample start: %s", sample_id)
        issues: List[str] = []

        if not fastp1:
            issues.append("MISSING_FASTP_R1")
        if not fastp2:
            issues.append("MISSING_FASTP_R2")
        if not depth:
            issues.append("MISSING_DEPTH")
        if not cns:
            issues.append("MISSING_CNS")
        if not annotated:
            issues.append("MISSING_ANNOTATED")

        generated = 0
        work_log: List[Tuple[str, str]] = []

        if not issues:
            with tempfile.TemporaryDirectory(prefix=f"mtb-evo-fig-{sample_id}-") as tmpdir:
                work = Path(tmpdir)
                for d in ["scripts", "fastp_qc", "alignment_qc", "variant_analysis", "figures", "qc_figures"]:
                    (work / d).mkdir(parents=True, exist_ok=True)

                shutil.copy2(qc_script, work / "scripts" / "generate_qc_figures.R")
                shutil.copy2(var_script, work / "scripts" / "generate_variant_figures.R")

                _safe_link_or_copy(fastp1, work / "fastp_qc" / f"{LEGACY_ALIAS}_1_fastp.json")
                _safe_link_or_copy(fastp2, work / "fastp_qc" / f"{LEGACY_ALIAS}_2_fastp.json")
                _safe_link_or_copy(depth, work / "alignment_qc" / f"{LEGACY_ALIAS}.depth")
                _safe_link_or_copy(cns, work / "variant_analysis" / f"{LEGACY_ALIAS}.cns")
                write_normalized_annotated_from_cns(
                    cns, annotated, work / "variant_analysis" / f"{LEGACY_ALIAS}_annotated.txt"
                )

                insert_ready = _prepare_insert_sizes(input_root, sample_id, work)
                if not insert_ready:
                    issues.append("MISSING_INSERT_SIZE")

                for cmd, name in [
                    (["Rscript", str(work / "scripts" / "generate_qc_figures.R")], "generate_qc_figures.R"),
                    (["Rscript", str(work / "scripts" / "generate_variant_figures.R")], "generate_variant_figures.R"),
                ]:
                    try:
                        proc = subprocess.run(
                            cmd,
                            cwd=work,
                            check=True,
                            capture_output=True,
                            text=True,
                        )
                        work_log.append((name, (proc.stdout or "") + (proc.stderr or "")))
                    except subprocess.CalledProcessError as e:
                        issues.append(f"SCRIPT_FAILED:{name}")
                        work_log.append(
                            (
                                name,
                                (e.stdout or "") + (e.stderr or ""),
                            )
                        )

                generated = _copy_figures(work / "figures", fig_dir, sample_id)

        if generated < 18:
            issues.append("PLOT_INCOMPLETE")

        status = "OK" if not issues else "PARTIAL_OK"

        with open(log_dir / f"report_figures_{sample_id}.log", "w", encoding="utf-8") as f:
            f.write(f"sample_id={sample_id}\n")
            f.write(f"status={status}\n")
            f.write(f"issues={';'.join(issues)}\n")
            f.write(f"generated_files={generated}\n")
            f.write(f"legacy_base={legacy_base}\n")
            for name, txt in work_log:
                f.write(f"\n[{name}]\n{txt}\n")

        logger.info("Figure sample done: %s status=%s generated=%s issues=%s", sample_id, status, generated, ";".join(issues))
        status_rows.append(
            {
                "sample_id": sample_id,
                "status": status,
                "issues": ";".join(issues),
                "generated_files": str(generated),
                "output_dir": str(fig_dir),
                "run_id": run_id,
                "stage": stage,
            }
        )

    status_output.parent.mkdir(parents=True, exist_ok=True)
    with open(status_output, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["sample_id", "status", "issues", "generated_files", "output_dir", "run_id", "stage"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(status_rows)

    logger.info("Figure status summary written to %s", status_output)
    return status_output


def report_figures_cmd(
    input_root: Path = Option(Path("results"), "--input-root", help="Input root with pipeline outputs"),
    output_root: Path = Option(Path("results/samples"), "--output-root", help="Output root for per-sample reports"),
    status_output: Path = Option(
        Path("results/logs/report_figures_status.tsv"), "--status-output", help="Status TSV output"
    ),
    legacy_base_dir: Optional[Path] = Option(
        None,
        "--legacy-base-dir",
        help="Legacy report template directory (contains scripts/generate_* files)",
    ),
    run_id: str = Option("", "--run-id", help="Run identifier stored in status metadata"),
) -> None:
    """Generate 01-09 report figures by calling original legacy scripts."""
    out = run_report_figures(
        input_root,
        output_root,
        status_output,
        legacy_base_dir=legacy_base_dir,
        run_id=run_id,
        stage="report_figures",
    )
    typer.echo(f"Figure status summary generated: {out}")
