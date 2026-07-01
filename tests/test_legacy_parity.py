from pathlib import Path

from src.commands.recall import recall_genotype


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_recall_outputs_n_when_var_is_an_indel(tmp_path: Path) -> None:
    loci = tmp_path / "diff_location.list"
    depth = tmp_path / "depth.txt"
    cns = tmp_path / "sample.cns"
    output = tmp_path / "sample.fas"

    loci.write_text("100\n")
    depth.write_text("10\n")
    cns.write_text(
        "Chrom\tPosition\tRef\tVar\tCons:Cov:Reads1:Reads2:Freq:P-value\n"
        "chr\t100\tA\tAT\tA:10:0:10:80%:0\n"
    )

    recall_genotype(loci, depth, cns, output)

    assert output.read_text() == ">sample\nN\n"


def test_snp_calling_keeps_legacy_ten_percent_depth_threshold() -> None:
    core_rule = (PROJECT_ROOT / "rules/core.smk").read_text()
    script_generator = (
        PROJECT_ROOT / "src/scripts/pair_fixed_nostrandbias.py"
    ).read_text()

    assert 'if [ "$min_cov" -lt 5 ]' not in core_rule
    assert "if [ $b -lt 5 ]" not in script_generator
