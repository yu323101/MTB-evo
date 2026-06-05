"""Shared variant normalization and classification helpers for figure/table reporting."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Tuple


SNP_BASES = {"A", "C", "G", "T"}
DEFAULT_ANNOT_ROW = ["-", "-", "-", "-", "---", "-", "-", "-", "-", "-"]


@dataclass(frozen=True)
class CnsVariant:
    """Single variant record from .cns used for report classification."""

    pos: str
    ref: str
    var: str

    @property
    def is_snp(self) -> bool:
        return self.var in SNP_BASES

    @property
    def is_indel(self) -> bool:
        return self.var.startswith("+") or self.var.startswith("-")

    @property
    def is_supported(self) -> bool:
        return self.is_snp or self.is_indel


@dataclass(frozen=True)
class VariantClassSummary:
    """Variant class counts based on CNS-main + expanded annotation backfill."""

    syn: int
    nonsyn: int
    intergenic: int
    snp: int
    indel: int

    @property
    def total(self) -> int:
        return self.snp + self.indel


def _iter_cns_variants(cns_file: Path) -> Iterator[CnsVariant]:
    with open(cns_file, "r", encoding="utf-8", errors="ignore") as fin:
        _ = fin.readline()  # header
        for line in fin:
            cols = line.rstrip("\n").split("\t")
            if len(cols) < 4:
                continue
            v = CnsVariant(pos=cols[1], ref=cols[2], var=cols[3])
            if v.is_supported:
                yield v


def _load_annotation_maps(annotated_file: Path) -> Tuple[Dict[Tuple[str, str], List[str]], Dict[str, List[str]]]:
    by_exact: Dict[Tuple[str, str], List[str]] = {}
    by_pos: Dict[str, List[str]] = {}
    with open(annotated_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            cols = line.rstrip("\n").split("\t")
            if len(cols) < 10:
                continue
            row = cols[:10]
            alt = row[2]
            pos_tokens = row[0].split("-")
            for pos in pos_tokens:
                by_exact.setdefault((pos, alt), row)
                by_pos.setdefault(pos, row)
    return by_exact, by_pos


def _resolve_annotation_row(
    variant: CnsVariant,
    by_exact: Dict[Tuple[str, str], List[str]],
    by_pos: Dict[str, List[str]],
) -> List[str]:
    base = by_exact.get((variant.pos, variant.var)) or by_pos.get(variant.pos)
    if base:
        row = list(base)
    else:
        row = list(DEFAULT_ANNOT_ROW)
        row[0] = variant.pos
        row[1] = variant.ref
        row[2] = variant.var

    if len(row) < 10:
        row += ["-"] * (10 - len(row))
    row = row[:10]

    if variant.is_indel:
        indel_type = "Insertion" if variant.var.startswith("+") else "Deletion"
        row[2] = indel_type
        row[4] = indel_type
    else:
        row[2] = variant.var
        if not (
            row[4] == "---"
            or row[4].startswith("Synonymous")
            or row[4].startswith("Nonsynonymous")
        ):
            row[4] = "---"
    return row


def normalized_rows_from_cns_and_annotation(cns_file: Path, annotated_file: Path) -> List[List[str]]:
    """Build normalized annotation rows using CNS as main table and expanded annotation backfill."""
    by_exact, by_pos = _load_annotation_maps(annotated_file)
    rows: List[List[str]] = []
    for variant in _iter_cns_variants(cns_file):
        rows.append(_resolve_annotation_row(variant, by_exact, by_pos))
    return rows


def write_normalized_annotated_from_cns(cns_file: Path, annotated_file: Path, out_file: Path) -> None:
    """Write normalized per-variant annotation text consumed by legacy report scripts."""
    rows = normalized_rows_from_cns_and_annotation(cns_file, annotated_file)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as fout:
        for row in rows:
            fout.write("\t".join(row) + "\n")


def summarize_variant_classes(cns_file: Path, annotated_file: Path) -> VariantClassSummary:
    """Summarize SNP/Indel and SNP functional classes from normalized rows."""
    syn = nonsyn = intergenic = 0
    snp = indel = 0

    for row in normalized_rows_from_cns_and_annotation(cns_file, annotated_file):
        mut_type = row[4] if len(row) >= 5 else "---"
        if mut_type in {"Insertion", "Deletion"}:
            indel += 1
            continue

        # Remaining rows in normalized output are SNP rows.
        snp += 1
        if mut_type == "---":
            intergenic += 1
        elif mut_type.startswith("Synonymous"):
            syn += 1
        elif mut_type.startswith("Nonsynonymous"):
            nonsyn += 1
        else:
            intergenic += 1

    return VariantClassSummary(
        syn=syn,
        nonsyn=nonsyn,
        intergenic=intergenic,
        snp=snp,
        indel=indel,
    )

