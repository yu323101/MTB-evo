"""Step 5: Merge FAS files into a single alignment."""

from pathlib import Path

import typer
from typer import Option

from src.utils.logging_config import get_logger


logger = get_logger("commands.merge")


def discover_recall_files(fas_dir: Path) -> list[Path]:
    candidates = []
    candidates.extend(sorted(fas_dir.glob("*.recall.fasta")))
    candidates.extend(sorted((fas_dir / "samples").glob("*/variant_analysis/*.recall.fasta")))
    candidates.extend(sorted(fas_dir.glob("*/variant_analysis/*.recall.fasta")))

    seen = set()
    recall_files = []
    for path in candidates:
        resolved = str(path.resolve())
        if resolved in seen:
            continue
        seen.add(resolved)
        recall_files.append(path)
    return recall_files


def merge_fas(fas_dir: Path, output: Path) -> None:
    """
    Merge all *.fas and *.fasta files into a single multi-sequence FASTA file.

    This function implements: cat *.fas *.fasta > all_strains.fa
    """
    # Prefer recall outputs; they are the intended equal-length alignment inputs.
    logger.info("Merging recall/alignment FASTA files from %s to %s", fas_dir, output)
    recall_files = discover_recall_files(fas_dir)
    if recall_files:
        fas_files = recall_files
    else:
        # Fallback for legacy usage, while excluding known non-alignment files.
        excluded_names = {output.name, "merged.fasta", "wildtype.fasta"}
        fas_files = [
            p
            for p in (sorted(fas_dir.glob("*.fas")) + sorted(fas_dir.glob("*.fasta")))
            if p.name not in excluded_names
        ]
    if not fas_files:
        raise ValueError(f"No .fas or .fasta files found in {fas_dir}")

    logger.info("Found %d FAS/FASTA files for merge", len(fas_files))
    typer.echo(f"Found {len(fas_files)} FAS/FASTA files")

    # Merge files
    with open(output, "w") as out_f:
        for fas_file in fas_files:
            with open(fas_file) as in_f:
                content = in_f.read()
                out_f.write(content)
                # Ensure file ends with newline
                if content and not content.endswith("\n"):
                    out_f.write("\n")

    logger.info("Merged %d files into %s", len(fas_files), output)
    typer.echo(f"Merged {len(fas_files)} files into {output}")


def merge_cmd(
    fas_dir: Path = Option(
        Path("."), "--fas-dir", "-f", help="Directory containing .fas/.fasta or samples/ layout"
    ),
    output: Path = Option(
        Path("all_strains.fa"), "--output", "-o", help="Output merged FASTA file"
    ),
) -> None:
    """Merge FAS files into a single alignment."""
    merge_fas(fas_dir, output)
    logger.info("Merge completed: %s", output)
    typer.echo(f"Merge completed: {output}")
