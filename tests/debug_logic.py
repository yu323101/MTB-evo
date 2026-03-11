"""Debug complete logic for position 46644."""

import re
from pathlib import Path

# Read loci
loci_file = Path("/Users/cosmos/Project/Allevo_script/test_data/input/diff_location.list")
with open(loci_file) as f:
    loci = [int(line.strip()) for line in f]

# Read depth
depth_file = Path("/Users/cosmos/Project/Allevo_script/test_data/input/depth.txt")
with open(depth_file) as f:
    avg_depth = int(f.read().strip())
depth_threshold = avg_depth * 0.1

print(f"Depth threshold: {depth_threshold}")

# Read CNS file
cns_file = Path("/Users/cosmos/Project/Allevo_script/test_data/raw/MD601.cns")
target_pos = 46644

with open(cns_file) as f:
    for line in f:
        if line.startswith("Chrom"):
            continue
        
        a = re.split(r'[\t:%]', line.strip())
        
        try:
            pos = int(a[1])
        except (ValueError, IndexError):
            continue
        
        if pos == target_pos:
            print(f"\nProcessing position {target_pos}:")
            
            ref = a[2]
            var = a[3]
            cons = a[4]
            cov_str = a[5]
            reads1_str = a[6]
            reads2_str = a[7]
            freq_str = a[8]
            
            print(f"  ref={ref}, var={var}, cons={cons}")
            print(f"  cov={cov_str}, reads1={reads1_str}, reads2={reads2_str}, freq={freq_str}")
            
            # Check conditions
            print("\n  Condition 1: len(cons) == 1")
            if len(cons) != 1:
                print("    FAILED")
                result = "N"
            else:
                print("    PASSED")
                
                print("  Condition 2: cov_str, reads1_str, reads2_str != '-'")
                if cov_str == "-" or reads1_str == "-" or reads2_str == "-":
                    print("    FAILED")
                    result = "N"
                else:
                    print("    PASSED")
                    
                    print("  Condition 3: cov > depth_threshold and cov >= 3")
                    cov = int(cov_str)
                    if cov <= depth_threshold or cov < 3:
                        print(f"    FAILED (cov={cov} <= {depth_threshold})")
                        result = "N"
                    else:
                        print(f"    PASSED (cov={cov} > {depth_threshold})")
                        
                        print("  Condition 4: real_ratio > 0.8")
                        reads1 = int(reads1_str)
                        reads2 = int(reads2_str)
                        real_ratio = (reads1 + reads2) / cov
                        print(f"    real_ratio = ({reads1} + {reads2}) / {cov} = {real_ratio}")
                        if real_ratio <= 0.8:
                            print("    FAILED")
                            result = "N"
                        else:
                            print("    PASSED")
                            
                            print("  Condition 5: frequency")
                            freq = int(freq_str)
                            print(f"    freq = {freq}")
                            if freq >= 75:
                                result = var if var != "." else cons
                                print(f"    Mutation: {result}")
                            elif freq <= 25:
                                result = ref
                                print(f"    Wild type: {result}")
                            else:
                                result = "?"
                                print(f"    Mixed: {result}")
            
            print(f"\n  Final result: {result}")
            print(f"  Expected: A")
            break
