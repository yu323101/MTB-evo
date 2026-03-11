#!/usr/bin/env perl
use warnings;

my $line = "gi|57116681|ref|NC_000962.2|\t1\tT\t.\tT:20:6:13:65%:5E0\tPass:0:0:0:0:1E0";

print "Original line:\n$line\n\n";

# Original Perl code
my @a = split "\t|:|%", $line;

print "Split by \"\\t|:\\|%%\" (original code):\n";
print "  Number of parts: " . scalar(@a) . "\n";
for (my $i = 0; $i <= 10 && $i <= $#a; $i++) {
    print "  a[$i] = '$a[$i]'\n";
}

print "\nKey indices:\n";
print "  a[1] (pos): $a[1]\n";
print "  a[2] (ref): $a[2]\n";
print "  a[3] (var): $a[3]\n";
print "  a[4] (cons info): $a[4]\n";
print "  a[5] (pass info): $a[5]\n";
