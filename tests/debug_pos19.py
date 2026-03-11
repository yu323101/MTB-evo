"""Debug position 19."""

from pathlib import Path

# Read loci
loci_file = Path("/Users/cosmos/Project/Allevo_script/test_data/input/diff_location.list")
with open(loci_file) as f:
    loci = [int(line.strip()) for line in f]

print(f"Position 19 in loci list: {loci[18]}")  # 0-indexed, so position 19 is index 18

# Check expected output
expected_file = Path("/Users/cosmos/Project/Allevo_script/test_data/output_expected/MD601.fas")
with open(expected_file) as f:
    lines = f.readlines()
    seq = lines[1].strip()
    print(f"Expected char at pos 19: {seq[18]}")

# Read CNS file
cns_file = Path("/Users/cosmos/Project/Allevo_script/test_data/raw/MD601.cns")
target_pos = loci[18]
print(f"\nLooking for position {target_pos} in CNS file...")

with open(cns_file) as f:
    for line_num, line in enumerate(f):
        if line.startswith("Chrom"):
            continue
        
        cols = line.strip().split("\t")
        
        try:
            pos = int(cols[1])
        except (ValueError, IndexError):
            continue
        
        if pos == target_pos:
            print(f"Found at line {line_num}")
            print(f"  cols[4] = {cols[4]}")
            
            cons_info = cols[4].split(":")
            print(f"  cons_info = {cons_info}")
            
            if len(cons_info) >= 6:
                cons = cons_info[0]
                cov = cons_info[1]
                reads1 = cons_info[2]
                reads2 = cons_info[3]
                freq = cons_info[4].rstrip("%")
                print(f"  cons={cons}, cov={cov}, reads1={reads1}, reads2={reads2}, freq={freq}")
            
            break
