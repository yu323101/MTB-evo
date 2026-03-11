"""Debug position 18 with new logic."""

from pathlib import Path

# Read loci
loci_file = Path("/Users/cosmos/Project/Allevo_script/test_data/input/diff_location.list")
with open(loci_file) as f:
    loci = [int(line.strip()) for line in f]

print(f"Position 18 in loci list: {loci[17]}")

# Read CNS file
cns_file = Path("/Users/cosmos/Project/Allevo_script/test_data/raw/MD601.cns")
target_pos = loci[17]

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
            print(f"  Number of columns: {len(cols)}")
            for i, col in enumerate(cols[:6]):
                print(f"  cols[{i}] = {col[:50]}...")
            
            ref = cols[2]
            var = cols[3]
            cons_info = cols[4].split(":")
            
            print(f"\n  Cons info parts: {cons_info}")
            print(f"  ref={ref}, var={var}")
            
            if len(cons_info) >= 6:
                cons = cons_info[0]
                cov = cons_info[1]
                reads1 = cons_info[2]
                reads2 = cons_info[3]
                freq = cons_info[4]
                print(f"  cons={cons}, cov={cov}, reads1={reads1}, reads2={reads2}, freq={freq}")
            
            break
