"""Lineage assignment (Perl-compatible with legacy lineage scripts)."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, List, Tuple

import typer
from typer import Option

from src.utils.logging_config import get_logger


logger = get_logger("commands.lineage")

LEGACY_MAJOR_MARKERS: Dict[int, str] = {
    615938: "L1",
    497491: "L2",
    2067684: "L23",
    3273107: "L3",
    1799921: "L5",
    1816587: "L6",
    1137518: "L7",
    3798451: "L411",
    3013784: "L412",
    4409231: "L413",
    2181026: "L42",
    1480024: "L43",
    3966059: "L44",
    2789341: "L45",
    990626: "L461",
    3506021: "L47",
}


def load_rules(rules_file: Path) -> Dict[int, str]:
    """Load lineage marker rules from TSV file: <position>\t<label>."""
    rules: Dict[int, str] = {}
    with open(rules_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            cols = line.split("\t")
            if len(cols) < 2:
                continue
            try:
                rules[int(cols[0])] = cols[1].strip()
            except ValueError:
                continue
    return rules


def discover_snp_files(snp_dir: Path) -> List[Path]:
    files: List[Path] = []
    files.extend(sorted(snp_dir.glob("*.snp")))
    files.extend(sorted((snp_dir / "samples").glob("*/variant_analysis/*.snp")))
    files.extend(sorted(snp_dir.glob("*/variant_analysis/*.snp")))
    # de-duplicate while preserving order
    uniq: List[Path] = []
    seen = set()
    for p in files:
        rp = str(p.resolve())
        if rp in seen:
            continue
        seen.add(rp)
        uniq.append(p)
    return uniq


def parse_snp_positions(snp_file: Path) -> List[int]:
    positions: List[int] = []
    with open(snp_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            cols = line.split()
            if not cols:
                continue
            try:
                positions.append(int(cols[0]))
            except ValueError:
                continue
    return positions


def _legacy_major_code(positions: List[int]) -> str:
    """Replicate lineage_assign.pl output code logic."""
    pos_set = set(positions)
    codes: List[str] = []
    for pos in sorted(pos_set):
        if pos in LEGACY_MAJOR_MARKERS and pos not in {497491, 264129}:
            codes.append(LEGACY_MAJOR_MARKERS[pos])
    if codes:
        # perl may print multiple lines due hash iteration; join as stable unique list
        return ",".join(dict.fromkeys(codes).keys())
    if 497491 in pos_set or 264129 in pos_set:
        return "L21" if 3309880 in pos_set else "L22"
    return "???"


def _split_rule_groups(rules: Dict[int, str]) -> Tuple[Dict[int, str], Dict[int, str], Dict[int, str], Dict[int, str], Dict[int, str]]:
    lin: Dict[int, str] = {}
    sub1: Dict[int, str] = {}
    sub2: Dict[int, str] = {}
    sub3: Dict[int, str] = {}
    sub4: Dict[int, str] = {}
    for pos, label in rules.items():
        if re.search(r"LINEAGE", label):
            lin[pos] = label
        elif re.search(r"lineage1", label):
            sub1[pos] = label
        elif re.search(r"lineage2", label):
            sub2[pos] = label
        elif re.search(r"lineage3", label):
            sub3[pos] = label
        elif re.search(r"lineage4", label):
            sub4[pos] = label
    return lin, sub1, sub2, sub3, sub4


def _pick_longest(current: str, candidate: str) -> str:
    if not current:
        return candidate
    return candidate if len(candidate) > len(current) else current


def _legacy_sublineage_assign(positions: List[int], rules: Dict[int, str]) -> Tuple[str, str]:
    """Replicate sublineage_assign.pl major/sublineage behavior."""
    pos_set = set(positions)
    lin, sub1, sub2, sub3, sub4 = _split_rule_groups(rules)

    lineage = ""
    sublineage = ""
    k = 0
    m = 0

    # perl iterates hash keys in arbitrary order; use sorted for deterministic output.
    for pos in sorted(pos_set):
        if pos in lin and lin[pos] != "LINEAGE4":
            if k > 0:
                if lineage != lin[pos]:
                    lineage = f"Heterozygosity_{lineage}-{lin[pos]}"
                    sublineage = f"Heterozygosity_{lineage}-{lin[pos]}"
            else:
                lineage = lin[pos]
                k = 1

    if k == 0:
        lineage = "LINEAGE4"
        for pos in sorted(pos_set):
            if pos in sub4 and sub4[pos] != "lineage4.9":
                if m > 0:
                    sublineage = _pick_longest(sublineage, sub4[pos])
                else:
                    sublineage = sub4[pos]
                    m += 1
        if m == 0:
            sublineage = "lineage4.9.x.x"

    if k == 1:
        if lineage == "LINEAGE1":
            for pos in sorted(pos_set):
                if pos in sub1 and sub1[pos] != "lineage1.1":
                    if m > 0:
                        sublineage = _pick_longest(sublineage, sub1[pos])
                    else:
                        sublineage = sub1[pos]
                        m += 1
            if m == 0:
                sublineage = "lineage1.x.x.x"

        if lineage == "LINEAGE2":
            for pos in sorted(pos_set):
                if pos in sub2 and sub2[pos] != "lineage2.2":
                    if m > 0:
                        sublineage = _pick_longest(sublineage, sub2[pos])
                    else:
                        sublineage = sub2[pos]
                        m += 1
            if m == 0:
                sublineage = "lineage2.x.x.x"

        if lineage == "LINEAGE3":
            for pos in sorted(pos_set):
                if pos in sub3:
                    if m > 0:
                        sublineage = _pick_longest(sublineage, sub3[pos])
                    else:
                        sublineage = sub3[pos]
                        m += 1
            if m == 0:
                sublineage = "lineage3.x.x.x"
            if "lineage3.1.2.1" in sublineage:
                sublineage = "lineage3.1.2.1"

        if lineage == "LINEAGE7":
            sublineage = "lineage7"
        if lineage == "LINEAGE6":
            sublineage = "lineage6"
        if lineage == "LINEAGE5":
            sublineage = "lineage5"

    return lineage, sublineage


def assign_lineage(positions: List[int], rules: Dict[int, str]) -> Tuple[str, str, int, int, int, str, str]:
    if not positions:
        return "", "", len(rules), 0, 0, "EMPTY_SNP", "SNP file is empty or invalid"

    major_code = _legacy_major_code(positions)
    major, sub = _legacy_sublineage_assign(positions, rules)
    hit_set = sorted({rules[pos] for pos in positions if pos in rules})

    heterozygosity_flag = 1 if major.startswith("Heterozygosity_") else 0
    status = "MULTI_LINEAGE" if heterozygosity_flag else "OK"
    message = ""
    if heterozygosity_flag:
        message = major
    elif major_code == "???":
        message = "No legacy major marker hit"
    elif major_code.startswith("L"):
        message = f"legacy_major_code={major_code}"

    return major, sub, len(rules), len(hit_set), heterozygosity_flag, status, message


def run_lineage(
    snp_dir: Path,
    rules: Path,
    output_summary: Path,
    run_id: str = "",
    stage: str = "lineage",
) -> Path:
    logger.info("Running lineage assignment from %s using rules %s", snp_dir, rules)
    snp_files = discover_snp_files(snp_dir)
    if not snp_files:
        raise ValueError(f"No .snp files found in {snp_dir}")

    rules_map = load_rules(rules)
    if not rules_map:
        raise ValueError(f"Rules file is empty or invalid: {rules}")

    output_summary.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    logger.info("Discovered %d SNP files for lineage assignment", len(snp_files))
    for snp_file in snp_files:
        sample_id = snp_file.stem
        positions = parse_snp_positions(snp_file)
        major, sub, total_markers, hit_markers, het_flag, status, message = assign_lineage(positions, rules_map)

        row = {
            "sample_id": sample_id,
            "lineage_major": major,
            "lineage_sub": sub,
            "method": "legacy_perl_compatible_v1",
            "marker_count_total": total_markers,
            "marker_count_hit": hit_markers,
            "heterozygosity_flag": het_flag,
            "status": status,
            "message": message,
            "run_id": run_id,
            "stage": stage,
        }
        summary_rows.append(row)
        logger.info("Lineage sample=%s major=%s sub=%s status=%s", sample_id, major, sub, status)

    with open(output_summary, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "sample_id",
                "lineage_major",
                "lineage_sub",
                "method",
                "marker_count_total",
                "marker_count_hit",
                "heterozygosity_flag",
                "status",
                "message",
                "run_id",
                "stage",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    logger.info("Lineage summary written to %s", output_summary)
    return output_summary


def lineage_cmd(
    snp_dir: Path = Option(Path("results"), "--snp-dir", help="Directory containing *.snp files"),
    rules: Path = Option(Path("data/lineage/typing_SNP.tsv"), "--rules", help="Lineage marker rules file"),
    output_summary: Path = Option(
        Path("results/logs/lineage_summary.tsv"),
        "--output-summary",
        help="Summary TSV output",
    ),
    run_id: str = Option("", "--run-id", help="Run identifier stored in output metadata"),
) -> None:
    """Assign lineage for all SNP files and write sample + summary outputs."""
    out = run_lineage(snp_dir, rules, output_summary, run_id=run_id, stage="lineage")
    typer.echo(f"Lineage summary generated: {out}")
