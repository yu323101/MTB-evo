"""Debug position 18."""

import re
from pathlib import Path

# Read loci
loci_file = Path("/Users/cosmos/Project/Allevo_script/test_data/input/diff_location.list")
with open(loci_file) as f:
    loci = [int(line.strip()) for line in f]

print(f"Position 18 in loci list: {loci[17]}")  # 0-indexed

# Read CNS file
cns_file = Path("/Users/cosmos/Project/Allevo_script/test_data/raw/MD601.cns")
target_pos = loci[17]

with open(cns_file) as f:
    for line in f:
        if line.startswith("Chrom"):
            continue
        
        # Split like Perl
        a = re.split(r'[\t:%]', line.strip())
        
        try:
            pos = int(a[1])
        except (ValueError, IndexError):
            continue
        
        if pos == target_pos:
            print(f"\nFound position {target_pos}:")
            print(f"  a[1] = {a[1]} (position)")
            print(f"  a[2] = {a[2]} (ref)")
            print(f"  a[3] = {a[3]} (var)")
            print(f"  a[4] = {a[4]} (cons)")
            print(f"  a[5] = {a[5]} (cov)")
            print(f"  a[6] = {a[6]} (reads1)")
            print(f"  a[7] = {a[7]} (reads2)")
            print(f"  a[8] = {a[8]} (freq)")
            
            # Check conditions
            print("\nCondition checks:")
            print(f"  len(a[3]) == 1: {len(a[3]) == 1}")
            print(f"  a[8] != '-': {a[8] != '-'}")
            
            try:
                cov = int(a[5])
                print(f"  cov = {cov}")
                print(f"  cov > 1: {cov > 1}")
                print(f"  cov >= 3: {cov >= 3}")
            except:
                print(f"  cov is not numeric: {a[5]}")
            
            break
