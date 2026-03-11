#!/usr/bin/env perl
use warnings;

my $line = "gi|57116681|ref|NC_000962.2|\t46644\tA\t.\tA:675:675:0:0%:1E0\tPass:0:0:0:0:1E0\t1\t0\t0\t0\tA:675:675:0:0%:1E0";

my @a = split "\t|:|%", $line;

print "Perl split result:\n";
for (my $i = 0; $i <= $#a; $i++) {
    print "  a[$i] = '$a[$i]'\n";
}

print "\nKey indices for position 46644:\n";
print "  a[1] (position): $a[1]\n";
print "  a[2] (ref): $a[2]\n";
print "  a[3] (var): $a[3]\n";
print "  a[5] (cov): $a[5]\n";
print "  a[6] (reads1): $a[6]\n";
print "  a[7] (reads2): $a[7]\n";
print "  a[8] (freq): $a[8]\n";
