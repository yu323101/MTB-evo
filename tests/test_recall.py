"""Test recall command against expected output."""

import tempfile
from pathlib import Path

from mtb_evo.commands.recall import recall_genotype


def test_recall_md601():
    """Test recall command with MD601 data."""
    # Paths to test data
    test_data_dir = Path("/Users/cosmos/Project/Allevo_script/test_data")
    loci_file = test_data_dir / "input" / "diff_location.list"
    depth_file = test_data_dir / "input" / "depth.txt"
    cns_file = test_data_dir / "raw" / "MD601.cns"
    expected_output = test_data_dir / "output_expected" / "MD601.fas"

    # Create temporary output file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".fas", delete=False) as f:
        output_file = Path(f.name)

    try:
        # Run recall
        recall_genotype(loci_file, depth_file, cns_file, output_file)

        # Compare with expected output
        with open(output_file) as f:
            actual = f.read()
        with open(expected_output) as f:
            expected = f.read()

        # Check if they match
        assert actual == expected, f"Output mismatch!\nExpected:\n{expected}\nActual:\n{actual}"
        print("✓ Test passed: MD601 recall output matches expected")

    finally:
        # Cleanup
        output_file.unlink()


if __name__ == "__main__":
    test_recall_md601()
