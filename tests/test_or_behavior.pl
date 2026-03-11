#!/usr/bin/env perl
use warnings;

# Test if | works as OR in split
my $line = "a:b|c";

print "Input: $line\n\n";

print "split /\\|/ (pipe only):\n";
my @a1 = split /\|/, $line;
print "  Result: " . join(", ", @a1) . "\n\n";

print "split /:|\\|/ (colon or pipe):\n";
my @a2 = split /:|\|/, $line;
print "  Result: " . join(", ", @a2) . "\n\n";

print "split /\\t|:|%/ (tab or colon or percent):\n";
my $line2 = "a:b\tc%d";
my @a3 = split /\t|:%/, $line2;
print "  Input: $line2\n";
print "  Result: " . join(", ", @a3) . "\n";
