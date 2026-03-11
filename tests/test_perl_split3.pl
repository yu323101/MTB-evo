#!/usr/bin/env perl
use warnings;

my $test = "gi|57116681|ref|NC_000962.2|\t1\tT";
print "Test string: $test\n\n";

# Split by different patterns
print "Split by \"\\t|:\" (tab, pipe, colon):\n";
my @a1 = split "\t|:", $test;
print "  Number of parts: " . scalar(@a1) . "\n";
print "  a1[0] = '$a1[0]'\n";
print "  a1[1] = '$a1[1]'\n\n";

print "Split by \"\\t\" (tab only):\n";
my @a2 = split "\t", $test;
print "  Number of parts: " . scalar(@a2) . "\n";
print "  a2[0] = '$a2[0]'\n";
print "  a2[1] = '$a2[1]'\n\n";

print "Split by /\\t|:/ (regex):\n";
my @a3 = split /\t|:/, $test;
print "  Number of parts: " . scalar(@a3) . "\n";
print "  a3[0] = '$a3[0]'\n";
print "  a3[1] = '$a3[1]'\n";
