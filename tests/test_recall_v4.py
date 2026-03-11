"""Test recall with Perl-compatible split."""

import re
from pathlib import Path


def recall_genotype(loci_file, depth_file, cns_file, output):
    """Back-calculate genotypes from CNS files."""
    # Step 1: Read differential loci list
    loci = []
    loci_set = set()
    genotype = {}

    with open(loci_file) as f:
        for line in f:
            pos = int(line.strip())
            loci.append(pos)
            loci_set.add(pos)
            genotype[pos] = "N"

    # Step 2: Read depth threshold
    with open(depth_file) as f:
        avg_depth = int(f.read().strip())
    depth_threshold = avg_depth * 0.1

    # Step 3: Parse CNS file
    # Perl: split "\t|:%", $_
    # This splits by tab, colon, or percent (but not pipe, because | in regex means OR)
    with open(cns_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("Chrom"):
                continue

            # Split by tab, colon, or percent
            # Note: In Perl "\t|:%", the | is literal, not regex OR
            # So it looks for the literal string "\t|:%" which doesn't exist
            # Actually, Perl treats it as a regex, so | means OR
            # But \t|:% means \t OR :%
            # Since :% doesn't exist in the data, only \t splits
            
            # Wait, let me re-check...
            # Actually, from my tests, split "\t|:%" splits by \t, :, or %
            # Because Perl compiles the string to a regex
            
            a = re.split(r'[\t:%]', line)
            if len(a) < 9:
                continue

            # Check if this is a differential locus
            try:
                pos = int(a[1])
            except ValueError:
                continue

            if pos not in loci_set:
                continue

            ref = a[2]
            var = a[3]
            cons = a[4]
            cov_str = a[5]
            reads1_str = a[6]
            reads2_str = a[7]
            freq_str = a[8]

            # Filter 1: Single base only
            if len(cons) != 1:
                genotype[pos] = "N"
                continue

            # Filter 2: No failed calls
            if cov_str == "-" or reads1_str == "-" or reads2_str == "-":
                genotype[pos] = "N"
                continue

            # Filter 3: Depth threshold
            try:
                cov = int(cov_str)
            except ValueError:
                genotype[pos] = "N"
                continue

            if cov <= depth_threshold or cov < 3:
                genotype[pos] = "N"
                continue

            # Filter 4: Real reads ratio > 80%
            try:
                reads1 = int(reads1_str)
                reads2 = int(reads2_str)
                real_ratio = (reads1 + reads2) / cov
            except (ValueError, ZeroDivisionError):
                genotype[pos] = "N"
                continue

            if real_ratio <= 0.8:
                genotype[pos] = "N"
                continue

            # Filter 5-7: Frequency-based
            try:
                freq = int(freq_str)
            except ValueError:
                genotype[pos] = "N"
                continue

            if freq >= 75:
                genotype[pos] = var if var != "." else cons
            elif freq <= 25:
                genotype[pos] = ref
            else:
                genotype[pos] = "?"

    # Step 4: Output
    sample_name = cns_file.stem.replace(".cns", "").replace(".raw", "")
    with open(output, "w") as f:
        f.write(f">{sample_name}\n")
        for pos in loci:
            f.write(genotype[pos])
        f.write("\n")


if __name__ == "__main__":
    # Test with MD601
    test_data_dir = Path("/Users/cosmos/Project/Allevo_script/test_data")
    loci_file = test_data_dir / "input" / "diff_location.list"
    depth_file = test_data_dir / "input" / "depth.txt"
    cns_file = test_data_dir / "raw" / "MD601.cns"
    output_file = Path("/tmp/test_md601_v4.fas")
    expected_file = test_data_dir / "output_expected" / "MD601.fas"

    recall_genotype(loci_file, depth_file, cns_file, output_file)

    # Compare
    with open(output_file) as f:
        actual = f.read()
    with open(expected_file) as f:
        expected = f.read()

    if actual == expected:
        print("✓ Test passed: Output matches expected")
    else:
        print("✗ Test failed: Output mismatch")
        print(f"Expected length: {len(expected)}")
        print(f"Actual length: {len(actual)}")

        # Find first difference
        lines_expected = expected.split("\n")
        lines_actual = actual.split("\n")

        if lines_expected[0] != lines_actual[0]:
            print(f"Header mismatch:")
            print(f"  Expected: {lines_expected[0]}")
            print(f"  Actual: {lines_actual[0]}")
        else:
            seq_expected = lines_expected[1] if len(lines_expected) > 1 else ""
            seq_actual = lines_actual[1] if len(lines_actual) > 1 else ""

            if len(seq_expected) != len(seq_actual):
                print(f"Sequence length mismatch: {len(seq_expected)} vs {len(seq_actual)}")

            for i, (e, a) in enumerate(zip(seq_expected, seq_actual)):
                if e != a:
                    print(f"First difference at position {i}: expected {repr(e)}, got {repr(a)}")
                    break
