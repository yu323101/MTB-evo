"""Debug position 19 full."""

from pathlib import Path

# Read loci
loci_file = Path("/Users/cosmos/Project/Allevo_script/test_data/input/diff_location.list")
with open(loci_file) as f:
    loci = [int(line.strip()) for line in f]

target_pos = loci[18]  # Position 19 (0-indexed)
print(f"Target position: {target_pos}")

# Read CNS file
cns_file = Path("/Users/cosmos/Project/Allevo_script/test_data/raw/MD601.cns")

with open(cns_file) as f:
    for line in f:
        if line.startswith("Chrom"):
            continue
        
        cols = line.strip().split("\t")
        
        try:
            pos = int(cols[1])
        except (ValueError, IndexError):
            continue
        
        if pos == target_pos:
            print(f"\nFound position {target_pos}:")
            print(f"  cols[2] (ref) = {cols[2]}")
            print(f"  cols[3] (var) = {cols[3]}")
            print(f"  cols[4] = {cols[4]}")
            
            ref = cols[2]
            var = cols[3]
            
            cons_info = cols[4].split(":")
            cons = cons_info[0]
            cov = int(cons_info[1])
            reads1 = int(cons_info[2])
            reads2 = int(cons_info[3])
            freq = float(cons_info[4].rstrip("%"))
            
            print(f"\n  cons={cons}, cov={cov}, reads1={reads1}, reads2={reads2}, freq={freq}")
            
            # Check conditions
            print(f"\n  len(cons) == 1: {len(cons) == 1}")
            print(f"  cov > 1.0: {cov > 1.0}")
            print(f"  cov >= 3: {cov >= 3}")
            
            real_ratio = (reads1 + reads2) / cov
            print(f"  real_ratio = {real_ratio}")
            print(f"  real_ratio > 0.8: {real_ratio > 0.8}")
            
            print(f"\n  freq >= 75: {freq >= 75}")
            print(f"  var: '{var}'")
            print(f"  var != '.': {var != '.'}")
            
            if freq >= 75:
                result = var if var != "." else cons
                print(f"\n  Result: mutation = {result}")
            
            break
