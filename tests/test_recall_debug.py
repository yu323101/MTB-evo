"""Test recall with debug output."""

from pathlib import Path


def recall_genotype(loci_file, depth_file, cns_file, output, debug_pos=None):
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

    # Step 3: Parse CNS file
    processed = 0
    with open(cns_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("Chrom"):
                continue

            cols = line.split("\t")
            if len(cols) < 11:
                continue

            try:
                pos = int(cols[1])
            except ValueError:
                continue

            if pos not in loci_set:
                continue

            processed += 1
            
            ref = cols[2]
            var = cols[3]
            
            # Cons info is in column 5 (index 4)
            cons_info = cols[4].split(":")
            if len(cons_info) < 6:
                genotype[pos] = "N"
                if pos == debug_pos:
                    print(f"DEBUG: pos={pos}, FAILED - cons_info length {len(cons_info)} < 6")
                continue

            cons = cons_info[0]
            cov_str = cons_info[1]
            reads1_str = cons_info[2]
            reads2_str = cons_info[3]
            freq_str = cons_info[4].rstrip("%")

            if pos == debug_pos:
                print(f"DEBUG: pos={pos}, ref={ref}, var={var}, cons={cons}")
                print(f"DEBUG: cov={cov_str}, reads1={reads1_str}, reads2={reads2_str}, freq={freq_str}")

            # Filter 1: Single base only
            if len(cons) != 1:
                genotype[pos] = "N"
                if pos == debug_pos:
                    print(f"DEBUG: pos={pos}, FAILED - len(cons)={len(cons)} != 1")
                continue

            # Filter 2: No failed calls
            if cov_str == "-" or reads1_str == "-" or reads2_str == "-":
                genotype[pos] = "N"
                if pos == debug_pos:
                    print(f"DEBUG: pos={pos}, FAILED - contains '-'")
                continue

            # Filter 3: Depth threshold
            try:
                cov = int(cov_str)
            except ValueError:
                genotype[pos] = "N"
                if pos == debug_pos:
                    print(f"DEBUG: pos={pos}, FAILED - cov_str '{cov_str}' not numeric")
                continue

            if cov <= depth_threshold or cov < 3:
                genotype[pos] = "N"
                if pos == debug_pos:
                    print(f"DEBUG: pos={pos}, FAILED - cov={cov} <= {depth_threshold} or < 3")
                continue

            # Filter 4: Real reads ratio > 80%
            try:
                reads1 = int(reads1_str)
                reads2 = int(reads2_str)
                real_ratio = (reads1 + reads2) / cov
            except (ValueError, ZeroDivisionError):
                genotype[pos] = "N"
                if pos == debug_pos:
                    print(f"DEBUG: pos={pos}, FAILED - reads not numeric or division by zero")
                continue

            if real_ratio <= 0.8:
                genotype[pos] = "N"
                if pos == debug_pos:
                    print(f"DEBUG: pos={pos}, FAILED - real_ratio={real_ratio} <= 0.8")
                continue

            # Filter 5-7: Frequency-based
            try:
                freq = int(freq_str)
            except ValueError:
                genotype[pos] = "N"
                if pos == debug_pos:
                    print(f"DEBUG: pos={pos}, FAILED - freq_str '{freq_str}' not numeric")
                continue

            if freq >= 75:
                genotype[pos] = var if var != "." else cons
                if pos == debug_pos:
                    print(f"DEBUG: pos={pos}, PASSED - mutation, result={genotype[pos]}")
            elif freq <= 25:
                genotype[pos] = ref
                if pos == debug_pos:
                    print(f"DEBUG: pos={pos}, PASSED - wild type, result={genotype[pos]}")
            else:
                genotype[pos] = "?"
                if pos == debug_pos:
                    print(f"DEBUG: pos={pos}, PASSED - mixed, result={genotype[pos]}")

    print(f"Processed {processed} loci")

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
    output_file = Path("/tmp/test_md601_debug.fas")

    recall_genotype(loci_file, depth_file, cns_file, output_file, debug_pos=46644)
