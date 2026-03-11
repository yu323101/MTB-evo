#!/usr/bin/env perl
use warnings;

# Test different split patterns
my $line = "gi|57116681|ref|NC_000962.2|\t46644\tA\t.\tA:675:675:0:0%:1E0";

print "Original line:\n$line\n\n";

# Pattern 1: "\t|:|%" (literal string)
my @a1 = split "\t|:|%", $line;
print "Split by \"\\t|:\\|%\" (literal):\n";
print "  Number of elements: " . scalar(@a1) . "\n";
print "  a1[0] = '$a1[0]'\n";
print "  a1[1] = '$a1[1]'\n";
print "  a1[4] = '$a1[4]'\n";
print "  a1[5] = '$a1[5]'\n\n";

# Pattern 2: /\t|:|%/ (regex)
my @a2 = split /\t|:|%/ , $line;
print "Split by /\\t|:\\|%/ (regex):\n";
print "  Number of elements: " . scalar(@a2) . "\n";
print "  a2[0] = '$a2[0]'\n";
print "  a2[1] = '$a2[1]'\n";
print "  a2[4] = '$a2[4]'\n";
print "  a2[5] = '$a2[5]'\n";
