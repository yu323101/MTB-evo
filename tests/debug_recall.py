"""Debug recall to understand the logic."""

import sys
from pathlib import Path

# Test with position 46644
test_data_dir = Path("/Users/cosmos/Project/Allevo_script/test_data")
cns_file = test_data_dir / "raw" / "MD601.cns"

# Find line with position 46644
with open(cns_file) as f:
    for line in f:
        if "46644" in line:
            print("CNS line:")
            print(line)
            print("\nSplit by tab:")
            cols = line.strip().split("\t")
            for i, col in enumerate(cols):
                print(f"  [{i}]: {col}")
            
            print("\nColumn 4 split by colon:")
            if len(cols) > 4:
                info = cols[4].split(":")
                for i, part in enumerate(info):
                    print(f"  [{i}]: {part}")
            break
