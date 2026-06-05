from __future__ import annotations

from pathlib import Path

from src.core.report_inputs import ANNOTATED_VARIANTS_DIRNAME, annotated_variant_candidates


def test_annotated_variant_candidates_prefers_new_dir(tmp_path: Path) -> None:
    sample_root = tmp_path / "results" / "samples" / "MD001.cleaned"
    new_dir = sample_root / "report_inputs" / ANNOTATED_VARIANTS_DIRNAME
    old_dir = sample_root / "report_inputs" / "variant_analysis"
    new_dir.mkdir(parents=True)
    old_dir.mkdir(parents=True)

    new_file = new_dir / "MD001.cleaned_annotated.txt"
    old_file = old_dir / "MD001.cleaned_annotated.txt"
    new_file.write_text("new\n", encoding="utf-8")
    old_file.write_text("old\n", encoding="utf-8")

    candidates = annotated_variant_candidates([sample_root], "MD001.cleaned")

    assert candidates[0] == new_file
    assert candidates[1] == old_file
