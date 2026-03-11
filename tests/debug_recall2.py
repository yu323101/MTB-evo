"""Debug recall to find the issue."""

import re
from pathlib import Path

test_data_dir = Path("/Users/cosmos/Project/Allevo_script/test_data")
cns_file = test_data_dir / "raw" / "MD601.cns"

# Read first few lines
with open(cns_file) as f:
    for i, line in enumerate(f):
        if i > 5:
            break
        line = line.strip()
        print(f"Line {i}: {line[:100]}...")
        
        if line.startswith("Chrom"):
            continue
            
        a = re.split(r'[\t:|%]', line)
        print(f"  Split into {len(a)} parts")
        print(f"  a[1]={a[1] if len(a)>1 else 'N/A'}, a[2]={a[2] if len(a)>2 else 'N/A'}")
        
        # Check if position 4429
        if len(a) > 1 and a[1] == "4429":
            print(f"  *** Found position 4429 ***")
            for j, part in enumerate(a[:15]):
                print(f"    a[{j}] = '{part}'")
