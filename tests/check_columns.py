"""Check column count."""

from pathlib import Path

cns_file = Path("/Users/cosmos/Project/Allevo_script/test_data/raw/MD601.cns")

with open(cns_file) as f:
    for i, line in enumerate(f):
        if i == 0:
            continue  # Skip header
        if i > 5:
            break
        
        cols = line.strip().split("\t")
        print(f"Line {i}: {len(cols)} columns")
        if len(cols) >= 5:
            print(f"  cols[1] = {cols[1]}")
            print(f"  cols[4] = {cols[4][:50]}...")
