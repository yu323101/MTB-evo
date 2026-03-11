"""Debug Perl split behavior."""

line = "gi|57116681|ref|NC_000962.2|\t46644\tA\t.\tA:675:675:0:0%:1E0\tPass:0:0:0:0:1E0\t1\t0\t0\t0\tA:675:675:0:0%:1E0"

# Perl: split "\t|:|%",$_
# This splits by tab, colon, OR pipe OR percent
import re
parts = re.split(r'[\t:|%]', line)
print("Perl split result:")
for i, part in enumerate(parts):
    print(f"  a[{i}] = '{part}'")

print("\nKey indices:")
print(f"  a[1] (Chromosome part 1): {parts[1]}")
print(f"  a[5] (Position): {parts[5]}")
print(f"  a[6] (Ref): {parts[6]}")
print(f"  a[7] (Var): {parts[7]}")
print(f"  a[8] (Cons): {parts[8]}")
print(f"  a[9] (Cov): {parts[9]}")
print(f"  a[10] (Reads1): {parts[10]}")
print(f"  a[11] (Reads2): {parts[11]}")
print(f"  a[12] (Freq): {parts[12]}")
