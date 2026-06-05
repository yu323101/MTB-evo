from __future__ import annotations

import csv
import subprocess
from pathlib import Path

from src.commands import report_tables
from src.commands.report_tables import _build_lineage_table, run_report_tables


def test_build_lineage_table_reads_run_specific_summary(tmp_path: Path) -> None:
    results_root = tmp_path / "results"
    lineage_dir = results_root / "logs" / "runs" / "latest"
    lineage_dir.mkdir(parents=True)
    lineage_tsv = lineage_dir / "lineage_summary.tsv"
    lineage_tsv.write_text(
        (
            "sample_id\tlineage_major\tlineage_sub\tmethod\tmarker_count_total\t"
            "marker_count_hit\theterozygosity_flag\tstatus\tmessage\trun_id\tstage\n"
            "MD001.cleaned\tLINEAGE2\tlineage2.2.1\tlegacy_perl_compatible_v1\t66\t3\t0\t"
            "OK\tlegacy_major_code=L23\tlatest\tlineage\n"
        ),
        encoding="utf-8",
    )
    out_csv = tmp_path / "lineage.csv"

    record = _build_lineage_table(results_root, "MD001.cleaned", out_csv, run_id="latest")

    assert record["status"] == "OK"
    assert record["lineage_major"] == "LINEAGE2"

    with open(out_csv, "r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    assert ["大谱系", "LINEAGE2", "主要谱系判定"] in rows


def test_run_report_tables_marks_missing_lineage_in_status(monkeypatch, tmp_path: Path) -> None:
    input_root = tmp_path / "results"
    sample_root = input_root / "samples" / "MD001.cleaned"
    (sample_root / "variant_analysis").mkdir(parents=True)
    (sample_root / "report_inputs" / "annotated_variants").mkdir(parents=True)

    cns = sample_root / "variant_analysis" / "MD001.cleaned.cns"
    annotated = sample_root / "report_inputs" / "annotated_variants" / "MD001.cleaned_annotated.txt"
    cns.write_text("Chrom\tPosition\tRef\tVar\n", encoding="utf-8")
    annotated.write_text("", encoding="utf-8")

    legacy_base = tmp_path / "legacy"
    scripts_dir = legacy_base / "scripts"
    scripts_dir.mkdir(parents=True)
    for name in ["generate_clinical_variant_report.py", "generate_variant_table_final.py"]:
        (scripts_dir / name).write_text("#!/usr/bin/env python3\n", encoding="utf-8")

    def fake_subprocess_run(cmd, cwd=None, check=None, capture_output=None, text=None):  # type: ignore[no-untyped-def]
        table_dir = Path(cwd) / "table"
        (table_dir / "临床变异检测报告_N24_1.csv").write_text("ok\n", encoding="utf-8")
        (table_dir / "样本级变异信息表_N24_1.csv").write_text("ok\n", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    def fake_quality(input_root: Path, sample_id: str, out_csv: Path) -> None:
        out_csv.write_text("ok\n", encoding="utf-8")

    def fake_clinical(cns_file: Path, annotated_file: Path, out_csv: Path) -> None:
        out_csv.write_text("ok\n", encoding="utf-8")

    monkeypatch.setattr(report_tables, "_resolve_legacy_base", lambda user_base=None: legacy_base)
    monkeypatch.setattr(report_tables.subprocess, "run", fake_subprocess_run)
    monkeypatch.setattr(report_tables, "_build_quality_table", fake_quality)
    monkeypatch.setattr(report_tables, "_build_clinical_variant_table_from_cns", fake_clinical)

    status_output = tmp_path / "report_tables_status.tsv"
    run_report_tables(input_root, input_root / "samples", status_output, run_id="latest")

    with open(status_output, "r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    assert rows[0]["status"] == "PARTIAL_OK"
    assert rows[0]["issues"] == "LINEAGE_STATUS:NO_LINEAGE_FILE"
