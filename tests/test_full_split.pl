#!/usr/bin/env perl
use warnings;

my $line = "gi|57116681|ref|NC_000962.2|\t1\tT\t.\tT:20:6:13:65%:5E0\tPass:0:0:0:0:1E0";

print "Full line:\n$line\n\n";

print "split \"\\t|:\\|%%\" on full line:\n";
my @a = split "\t|:%", $line;
print "  Total parts: " . scalar(@a) . "\n";
for (my $i = 0; $i <= 15 && $i <= $#a; $i++) {
    print "  a[$i] = '$a[$i]'\n";
}

print "\nSo for position 1:\n";
print "  a[1] = '$a[1]' (position)\n";
print "  a[2] = '$a[2]' (ref)\n";
print "  a[3] = '$a[3]' (var)\n";
print "  a[4] = '$a[4]' (cons)\n";
print "  a[5] = '$a[5]' (cov)\n";
print "  a[6] = '$a[6]' (reads1)\n";
print "  a[7] = '$a[7]' (reads2)\n";
print "  a[8] = '$a[8]' (freq)\n";
