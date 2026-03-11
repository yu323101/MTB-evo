"""Debug position 19 in test_recall_v6."""

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
    target_pos = 54954  # Position 19 in loci list
    
    with open(cns_file) as f:
        for line_num, line in enumerate(f):
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

            if pos != target_pos:
                continue

            print(f"Found position {target_pos} at line {line_num}")
            
            ref = cols[2]
            var = cols[3]
            
            print(f"  ref={ref}, var={var}")
            print(f"  cols[4]={cols[4]}")
            
            # Cons info is in column 5 (index 4)
            cons_info = cols[4].split(":")
            print(f"  cons_info={cons_info}")
            print(f"  len(cons_info)={len(cons_info)}")
            
            if len(cons_info) < 6:
                print("  FAILED: len(cons_info) < 6")
                genotype[pos] = "N"
                continue

            cons = cons_info[0]
            cov_str = cons_info[1]
            reads1_str = cons_info[2]
            reads2_str = cons_info[3]
            freq_str = cons_info[4].rstrip("%")
            
            print(f"  cons={cons}, cov_str={cov_str}, reads1_str={reads1_str}, reads2_str={reads2_str}, freq_str={freq_str}")

            # Filter 1: Single base only
            if len(cons) != 1:
                print(f"  FAILED: len(cons)={len(cons)} != 1")
                genotype[pos] = "N"
                continue

            # Filter 2: No failed calls
            if cov_str == "-" or reads1_str == "-" or reads2_str == "-":
                print("  FAILED: contains '-'")
                genotype[pos] = "N"
                continue

            # Filter 3: Depth threshold
            try:
                cov = int(cov_str)
            except ValueError:
                print(f"  FAILED: cov_str '{cov_str}' not numeric")
                genotype[pos] = "N"
                continue

            print(f"  cov={cov}, depth_threshold={depth_threshold}")
            
            if cov <= depth_threshold or cov < 3:
                print(f"  FAILED: cov={cov} <= {depth_threshold} or < 3")
                genotype[pos] = "N"
                continue

            # Filter 4: Real reads ratio > 80%
            try:
                reads1 = int(reads1_str)
                reads2 = int(reads2_str)
                real_ratio = (reads1 + reads2) / cov
            except (ValueError, ZeroDivisionError):
                print("  FAILED: reads not numeric or division by zero")
                genotype[pos] = "N"
                continue

            print(f"  reads1={reads1}, reads2={reads2}, real_ratio={real_ratio}")
            
            if real_ratio <= 0.8:
                print(f"  FAILED: real_ratio={real_ratio} <= 0.8")
                genotype[pos] = "N"
                continue

            # Filter 5-7: Frequency-based
            try:
                freq = int(float(freq_str))  # Handle float like 99.86
            except ValueError:
                print(f"  FAILED: freq_str '{freq_str}' not numeric")
                genotype[pos] = "N"
                continue

            print(f"  freq={freq}")
            
            if freq >= 75:
                genotype[pos] = var if var != "." else cons
                print(f"  PASSED: mutation, result={genotype[pos]}")
            elif freq <= 25:
                genotype[pos] = ref
                print(f"  PASSED: wild type, result={genotype[pos]}")
            else:
                genotype[pos] = "?"
                print(f"  PASSED: mixed, result={genotype[pos]}")

            break

    print(f"\nFinal genotype for {target_pos}: {genotype.get(target_pos, 'NOT SET')}")


if __name__ == "__main__":
    test_data_dir = Path("/Users/cosmos/Project/Allevo_script/test_data")
    loci_file = test_data_dir / "input" / "diff_location.list"
    depth_file = test_data_dir / "input" / "depth.txt"
    cns_file = test_data_dir / "raw" / "MD601.cns"

    recall_genotype(loci_file, depth_file, cns_file, None)
