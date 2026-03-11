"""Test recall v5 with debug."""

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

    print(f"Depth threshold: {depth_threshold}")
    print(f"Total loci: {len(loci)}")
    print(f"First few loci: {loci[:5]}")

    # Step 3: Parse CNS file
    found_count = 0
    with open(cns_file) as f:
        for line_num, line in enumerate(f):
            line = line.strip()
            if not line or line.startswith("Chrom"):
                continue

            cols = line.split("\t")
            if len(cols) < 11:
                print(f"Line {line_num}: only {len(cols)} columns, skipping")
                continue

            try:
                pos = int(cols[1])
            except ValueError:
                continue

            if pos not in loci_set:
                continue

            found_count += 1
            
            if pos == 46644:
                print(f"\nFound position 46644 at line {line_num}")
                print(f"  cols[2] = {cols[2]}")
                print(f"  cols[3] = {cols[3]}")
                print(f"  cols[4] = {cols[4]}")
                
                cons_info = cols[4].split(":")
                print(f"  cons_info = {cons_info}")
                print(f"  len(cons_info) = {len(cons_info)}")

            ref = cols[2]
            var = cols[3]
            
            # Cons info is in column 5 (index 4)
            # Format: Cons:Cov:Reads1:Reads2:Freq:P-value
            cons_info = cols[4].split(":")
            if len(cons_info) < 6:
                genotype[pos] = "N"
                if pos == 46644:
                    print(f"  FAILED: len(cons_info) = {len(cons_info)} < 6")
                continue

            cons = cons_info[0]
            cov_str = cons_info[1]
            reads1_str = cons_info[2]
            reads2_str = cons_info[3]
            freq_str = cons_info[4].rstrip("%")

            if pos == 46644:
                print(f"  cons={cons}, cov={cov_str}, reads1={reads1_str}, reads2={reads2_str}, freq={freq_str}")

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
                if pos == 46644:
                    print(f"  FAILED: cov={cov} <= {depth_threshold}")
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
                freq = int(float(freq_str))  # Handle float frequencies like 99.86
            except ValueError:
                genotype[pos] = "N"
                continue

            if freq >= 75:
                genotype[pos] = var if var != "." else cons
            elif freq <= 25:
                genotype[pos] = ref
                if pos == 46644:
                    print(f"  PASSED: wild type, result={ref}")
            else:
                genotype[pos] = "?"

    print(f"\nFound {found_count} loci in CNS file")
    print(f"Genotype for 46644: {genotype.get(46644, 'NOT SET')}")

    # Step 4: Output
    sample_name = cns_file.stem.replace(".cns", "").replace(".raw", "")
    with open(output, "w") as f:
        f.write(f">{sample_name}\n")
        for pos in loci:
            f.write(genotype[pos])
        f.write("\n")


if __name__ == "__main__":
    test_data_dir = Path("/Users/cosmos/Project/Allevo_script/test_data")
    loci_file = test_data_dir / "input" / "diff_location.list"
    depth_file = test_data_dir / "input" / "depth.txt"
    cns_file = test_data_dir / "raw" / "MD601.cns"
    output_file = Path("/tmp/test_md601_v6.fas")

    recall_genotype(loci_file, depth_file, cns_file, output_file)
