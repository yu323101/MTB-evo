"""Compare legacy core outputs with shared core outputs."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

import typer
from typer import Option


def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _discover_samples(root: Path) -> List[str]:
    samples_dir = root / "samples"
    if not samples_dir.exists():
        return []
    return sorted(p.name for p in samples_dir.iterdir() if p.is_dir())


def _sample_file_pairs_for_sample(sample_id: str) -> List[Tuple[str, str, str]]:
    return [
        (
            f"samples/{sample_id}/alignment_qc/{sample_id}.sort.bam",
            f"samples/{sample_id}/alignment_qc/{sample_id}.sort.bam",
            "alignment_sort_bam",
        ),
        (
            f"samples/{sample_id}/variant_analysis/{sample_id}.cns",
            f"samples/{sample_id}/variant_analysis/{sample_id}.cns",
            "variant_cns",
        ),
        (
            f"samples/{sample_id}/variant_analysis/{sample_id}.vars",
            f"samples/{sample_id}/variant_analysis/{sample_id}.vars",
            "variant_vars",
        ),
        (
            f"samples/{sample_id}/variant_analysis/{sample_id}.snp",
            f"samples/{sample_id}/variant_analysis/{sample_id}.snp",
            "variant_snp",
        ),
        (
            f"samples/{sample_id}/report_inputs/fastp_qc/{sample_id}_1_fastp.json",
            f"samples/{sample_id}/report_inputs/fastp_qc/{sample_id}_1_fastp.json",
            "fastp_json_r1",
        ),
        (
            f"samples/{sample_id}/report_inputs/fastp_qc/{sample_id}_2_fastp.json",
            f"samples/{sample_id}/report_inputs/fastp_qc/{sample_id}_2_fastp.json",
            "fastp_json_r2",
        ),
    ]


def _shared_core_pairs_for_sample(sample_id: str) -> List[Tuple[str, str, str]]:
    return [
        (
            f"samples/{sample_id}/core/diff_loci.txt",
            "core/diff_loci.txt",
            "core_diff_loci",
        ),
        (
            f"samples/{sample_id}/core/merged.fasta",
            "core/merged.fasta",
            "core_merged_fasta",
        ),
        (
            f"samples/{sample_id}/core/wildtype.fasta",
            "core/wildtype.fasta",
            "core_wildtype_fasta",
        ),
        (
            f"samples/{sample_id}/core/core_snps.fadel-InvMisF5.bak.fa",
            "core/core_snps.fadel-InvMisF5.bak.fa",
            "core_snps_fa",
        ),
        (
            f"samples/{sample_id}/core/core_snps.fadel-InvMisF5.bak.loc",
            "core/core_snps.fadel-InvMisF5.bak.loc",
            "core_snps_loc",
        ),
        (
            f"samples/{sample_id}/core/distance_matrix.txt",
            "core/distance_matrix.txt",
            "core_distance_matrix",
        ),
    ]


def _compare_pair(legacy_file: Path, new_file: Path) -> Tuple[str, str, str, str, str, str]:
    legacy_exists = legacy_file.exists()
    new_exists = new_file.exists()

    legacy_hash = ""
    new_hash = ""
    note = ""

    if legacy_exists and new_exists:
        legacy_hash = _sha256(legacy_file)
        new_hash = _sha256(new_file)
        if legacy_hash == new_hash:
            status = "PASS"
        else:
            status = "FAIL"
            note = "HASH_MISMATCH"
    elif (not legacy_exists) and (not new_exists):
        status = "PASS"
        note = "BOTH_MISSING"
    else:
        status = "FAIL"
        note = "FILE_MISSING_IN_ONE_SIDE"

    return status, str(legacy_exists), str(new_exists), legacy_hash, new_hash, note


def compare_core_outputs(legacy_root: Path, new_root: Path, output: Path) -> Dict[str, int]:
    legacy_samples = set(_discover_samples(legacy_root))
    new_samples = set(_discover_samples(new_root))
    all_samples = sorted(legacy_samples.union(new_samples))

    rows: List[Dict[str, str]] = []
    summary = {"total": 0, "pass": 0, "fail": 0}

    for sample_id in all_samples:
        for legacy_rel, new_rel, category in _sample_file_pairs_for_sample(sample_id):
            legacy_file = legacy_root / legacy_rel
            new_file = new_root / new_rel
            status, legacy_exists, new_exists, legacy_hash, new_hash, note = _compare_pair(
                legacy_file, new_file
            )

            summary["total"] += 1
            if status == "PASS":
                summary["pass"] += 1
            else:
                summary["fail"] += 1

            rows.append(
                {
                    "sample_id": sample_id,
                    "category": category,
                    "relative_path": legacy_rel if legacy_rel == new_rel else f"{legacy_rel} => {new_rel}",
                    "status": status,
                    "legacy_exists": legacy_exists,
                    "new_exists": new_exists,
                    "legacy_sha256": legacy_hash,
                    "new_sha256": new_hash,
                    "note": note,
                }
            )

    # Shared core outputs are compared against each legacy per-sample core copy.
    for sample_id in all_samples:
        for legacy_rel, new_rel, category in _shared_core_pairs_for_sample(sample_id):
            legacy_file = legacy_root / legacy_rel
            new_file = new_root / new_rel
            status, legacy_exists, new_exists, legacy_hash, new_hash, note = _compare_pair(
                legacy_file, new_file
            )

            summary["total"] += 1
            if status == "PASS":
                summary["pass"] += 1
            else:
                summary["fail"] += 1

            rows.append(
                {
                    "sample_id": sample_id,
                    "category": category,
                    "relative_path": f"{legacy_rel} => {new_rel}",
                    "status": status,
                    "legacy_exists": legacy_exists,
                    "new_exists": new_exists,
                    "legacy_sha256": legacy_hash,
                    "new_sha256": new_hash,
                    "note": note,
                }
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "sample_id",
                "category",
                "relative_path",
                "status",
                "legacy_exists",
                "new_exists",
                "legacy_sha256",
                "new_sha256",
                "note",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)

    return summary


def compare_core_cmd(
    legacy_root: Path = Option(..., "--legacy-root", help="Legacy run-core results root"),
    new_root: Path = Option(..., "--new-root", help="New sample-rule core results root"),
    output: Path = Option(
        Path("results/logs/workflow/core_compat_report.tsv"),
        "--output",
        help="Compatibility report TSV",
    ),
) -> None:
    """Compare legacy run-core and new shared-core outputs."""
    summary = compare_core_outputs(legacy_root, new_root, output)
    typer.echo(f"Compatibility report: {output}")
    typer.echo(
        f"Compared={summary['total']} PASS={summary['pass']} FAIL={summary['fail']}"
    )
    if summary["fail"] > 0:
        raise typer.Exit(code=1)
