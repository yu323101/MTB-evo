from __future__ import annotations

from pathlib import Path


def test_repo_samplesheet_is_template_not_machine_specific() -> None:
    samplesheet = Path(__file__).resolve().parents[1] / "config" / "samplesheet.csv"
    text = samplesheet.read_text(encoding="utf-8")

    assert "/data/projects/" not in text
    assert "/path/to/" in text
