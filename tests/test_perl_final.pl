#!/usr/bin/env perl
use warnings;

my $line = "gi|57116681|ref|NC_000962.2|\t1\tT\t.\tT:20:6:13:65%:5E0";

print "Line: $line\n\n";

# Test different interpretations
print "Interpretation 1: split by characters in string '\t|:%'\n";
my @a1 = split /[\t:|%]/, $line;
print "  Count: " . scalar(@a1) . "\n";
print "  a[0] = '$a1[0]'\n";
print "  a[1] = '$a1[1]'\n\n";

print "Interpretation 2: split by literal string \"\\t|:%\"\n";
my @a2 = split "\t|:%", $line;
print "  Count: " . scalar(@a2) . "\n";
print "  a[0] = '$a2[0]'\n";
print "  a[1] = '$a2[1]'\n\n";

print "Original code: split \"\\t|:\\|%%\"\n";
my @a3 = split "\t|:%", $line;
print "  Count: " . scalar(@a3) . "\n";
print "  a[0] = '$a3[0]'\n";
print "  a[1] = '$a3[1]'\n";
