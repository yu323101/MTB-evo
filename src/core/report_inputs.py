"""Prepare sample-scoped foundation outputs and downstream bridge inputs."""

from __future__ import annotations

import csv
import shutil
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Iterable, List


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ANNOTATION_ASSET_DIR = PROJECT_ROOT / "data" / "report_assets" / "annotation"
ANNOTATION_SCRIPT_CANDIDATES = []
if os.environ.get("MTB_EVO_ANNOTATION_SCRIPT"):
    ANNOTATION_SCRIPT_CANDIDATES.append(Path(os.environ["MTB_EVO_ANNOTATION_SCRIPT"]))
ANNOTATION_SCRIPT_CANDIDATES.append(
    ANNOTATION_ASSET_DIR / "0_MTBC_Annotation_mtbc_4411532_corrected.pl"
)


def parse_samples_input(samples_file: Path) -> List[Dict[str, str]]:
    """Parse a legacy samples.txt or CSV samplesheet."""
    base_dir = samples_file.parent.resolve()
    with open(samples_file, "r", encoding="utf-8") as f:
        first = f.readline().strip()

    rows: List[Dict[str, str]] = []
    if "," in first and "sample_id" in first.lower() and "r1" in first.lower() and "r2" in first.lower():
        with open(samples_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sample_id = str(row.get("sample_id", "")).strip()
                r1 = str(row.get("r1", "")).strip()
                r2 = str(row.get("r2", "")).strip()
                if sample_id and r1 and r2:
                    rows.append(
                        {
                            "sample_id": sample_id,
                            "r1": str((base_dir / r1).resolve()) if not Path(r1).is_absolute() else r1,
                            "r2": str((base_dir / r2).resolve()) if not Path(r2).is_absolute() else r2,
                        }
                    )
    else:
        with open(samples_file, "r", encoding="utf-8") as f:
            for line in f:
                prefix = line.strip()
                if not prefix:
                    continue
                prefix_path = Path(prefix)
                if not prefix_path.is_absolute():
                    prefix_path = (base_dir / prefix_path).resolve()
                sample_id = prefix_path.name
                rows.append(
                    {
                        "sample_id": sample_id,
                        "r1": str(prefix_path) + "_1.fastq.gz",
                        "r2": str(prefix_path) + "_2.fastq.gz",
                    }
                )
    return rows


def write_fastp_json(fastq_path: Path, output_json: Path, output_html: Path) -> None:
    fastp = shutil.which("fastp")
    if not fastp:
        raise RuntimeError("fastp not found in PATH")

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_html.parent.mkdir(parents=True, exist_ok=True)

    threads = max(1, min(4, os.cpu_count() or 1))
    with tempfile.TemporaryDirectory(prefix="mtb-evo-fastp-") as tmpdir:
        tmp_out = Path(tmpdir) / f"{fastq_path.stem}.fastq.gz"
        cmd = [
            fastp,
            "-i",
            str(fastq_path),
            "-o",
            str(tmp_out),
            "-j",
            str(output_json),
            "-h",
            str(output_html),
            "-w",
            str(threads),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def _run_to_file(cmd: List[str], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        subprocess.run(cmd, check=True, stdout=f, stderr=subprocess.PIPE, text=True)


def _extract_flagstat_value(lines: Iterable[str], keyword: str) -> int:
    for line in lines:
        if keyword in line:
            parts = line.strip().split()
            if parts:
                try:
                    return int(parts[0])
                except ValueError:
                    return 0
    return 0


def write_dedup_metrics(flagstat_file: Path, output_file: Path) -> None:
    lines = flagstat_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    total_reads = _extract_flagstat_value(lines, "in total")
    duplicate_reads = _extract_flagstat_value(lines, "duplicates")
    duplication = (duplicate_reads / total_reads) if total_reads else 0.0

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(
            "LIBRARY\tUNPAIRED_READS_EXAMINED\tREAD_PAIRS_EXAMINED\tUNMAPPED_READS\t"
            "UNPAIRED_READ_DUPLICATES\tREAD_PAIR_DUPLICATES\tREAD_PAIR_OPTICAL_DUPLICATES\t"
            "PERCENT_DUPLICATION\tESTIMATED_LIBRARY_SIZE\n"
        )
        f.write(
            f"UnknownLibrary\t0\t0\t0\t{duplicate_reads}\t0\t0\t{duplication:.6f}\t0\n"
        )


def write_insert_size_metrics(stats_file: Path, metrics_file: Path, inserts_file: Path) -> None:
    metrics_file.parent.mkdir(parents=True, exist_ok=True)
    inserts_file.parent.mkdir(parents=True, exist_ok=True)

    lines = stats_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    with open(metrics_file, "w", encoding="utf-8") as metrics_out, open(
        inserts_file, "w", encoding="utf-8"
    ) as inserts_out:
        for line in lines:
            if not line.startswith("IS\t"):
                continue
            metrics_out.write(f"{line}\n")
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            try:
                insert_size = int(parts[1])
                count = int(parts[2])
            except ValueError:
                continue
            if count <= 0:
                continue
            for _ in range(count):
                inserts_out.write(f"{insert_size}\n")


def _find_annotation_script() -> Path:
    for script in ANNOTATION_SCRIPT_CANDIDATES:
        if script.exists():
            return script
    raise FileNotFoundError("Annotation script not found in configured locations")


def write_annotated_from_cns(cns_file: Path, output_file: Path) -> None:
    annotation_script = _find_annotation_script()
    perl_path = shutil.which("perl")
    if not perl_path:
        raise RuntimeError("perl not found in PATH")

    snp_rows: List[str] = []
    indel_rows: List[str] = []

    with open(cns_file, "r", encoding="utf-8", errors="ignore") as f:
        _ = f.readline()
        for line in f:
            cols = line.rstrip("\n").split("\t")
            if len(cols) < 4:
                continue
            pos, ref, var = cols[1], cols[2], cols[3]
            if var in {"A", "C", "G", "T"}:
                snp_rows.append(f"{pos}\t{ref}\t{var}\n")
            elif var.startswith("+") or var.startswith("-"):
                indel_type = "Insertion" if var.startswith("+") else "Deletion"
                indel_rows.append(f"{pos}\t{ref}\t{var}\t-\t{indel_type}\t-\t-\t-\t-\t-\n")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mtb-evo-annot-") as tmpdir:
        tmpdir_path = Path(tmpdir)
        snp_input = tmpdir_path / "snp_input.txt"
        snp_output = tmpdir_path / "snp_annotated.txt"
        snp_input.write_text("".join(snp_rows), encoding="utf-8")

        if snp_rows:
            with open(snp_output, "w", encoding="utf-8") as out:
                subprocess.run(
                    [perl_path, str(annotation_script), str(snp_input)],
                    check=True,
                    stdout=out,
                    stderr=subprocess.PIPE,
                    text=True,
                )

        with open(output_file, "w", encoding="utf-8") as out:
            if snp_output.exists():
                snp_text = snp_output.read_text(encoding="utf-8", errors="ignore")
                out.write(snp_text)
                if snp_text and not snp_text.endswith("\n") and indel_rows:
                    out.write("\n")
            for row in indel_rows:
                out.write(row)


def prepare_sample_foundation_outputs(sample_id: str, r1: Path, r2: Path, sample_dir: Path) -> None:
    foundation_dir = sample_dir / "report_inputs" / "fastp_qc"
    write_fastp_json(
        r1,
        foundation_dir / f"{sample_id}_1_fastp.json",
        foundation_dir / f"{sample_id}_1_fastp.html",
    )
    write_fastp_json(
        r2,
        foundation_dir / f"{sample_id}_2_fastp.json",
        foundation_dir / f"{sample_id}_2_fastp.html",
    )


def prepare_sample_downstream_inputs_from_results(sample_id: str, sample_dir: Path, samtools: Path) -> None:
    downstream_align_dir = sample_dir / "report_inputs" / "alignment_qc"
    downstream_variant_dir = sample_dir / "report_inputs" / "variant_analysis"
    alignment_dir = sample_dir / "alignment_qc"
    variant_dir = sample_dir / "variant_analysis"

    bam_file = alignment_dir / f"{sample_id}.sort.bam"
    cns_file = variant_dir / f"{sample_id}.cns"
    if not bam_file.exists():
        raise FileNotFoundError(f"BAM not found for {sample_id}: {bam_file}")
    if not cns_file.exists():
        raise FileNotFoundError(f"CNS not found for {sample_id}: {cns_file}")

    bai_file = alignment_dir / f"{sample_id}.sort.bam.bai"
    if not bai_file.exists():
        subprocess.run([str(samtools), "index", str(bam_file)], check=True)

    depth_file = downstream_align_dir / f"{sample_id}.depth"
    _run_to_file([str(samtools), "depth", str(bam_file)], depth_file)

    bam_stat_out = alignment_dir / f"{sample_id}_bam_stat.out"
    _run_to_file([str(samtools), "flagstat", str(bam_file)], bam_stat_out)

    samtools_stats = alignment_dir / "samtools_stats.txt"
    _run_to_file([str(samtools), "stats", str(bam_file)], samtools_stats)

    write_dedup_metrics(bam_stat_out, alignment_dir / "dedup_metrics.txt")
    write_insert_size_metrics(
        samtools_stats,
        alignment_dir / "insert_size_metrics.txt",
        downstream_align_dir / "insert_sizes.txt",
    )

    write_annotated_from_cns(cns_file, downstream_variant_dir / f"{sample_id}_annotated.txt")

