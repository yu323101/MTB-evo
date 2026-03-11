#!/usr/bin/env perl
use warnings;

my $line = "gi|57116681|ref|NC_000962.2|\t46644\tA\t.\tA:675:675:0:0%:1E0\tPass:0:0:0:0:1E0\t1\t0\t0\t0\tA:675:675:0:0%:1E0";

print "Full CNS line:\n$line\n\n";

my @a = split "\t|:%", $line;

print "split result:\n";
for (my $i = 0; $i <= $#a; $i++) {
    print "  a[$i] = '$a[$i]'\n";
}

print "\nSo for original code using a[5], a[6], a[7], a[8]:\n";
print "  These come from the SECOND cons info column (a[10])\n";
print "  a[10] = '$a[10]'\n";
print "  a[11] = '$a[11]'\n";
print "  a[12] = '$a[12]'\n";
print "  a[13] = '$a[13]'\n";
print "  a[14] = '$a[14]'\n";
print "  a[15] = '$a[15]'\n";
