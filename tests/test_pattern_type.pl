#!/usr/bin/env perl
use warnings;

# Test if "\t|:%" is treated as regex
my $line = "A:675:675:0:0%:1E0";

print "String: $line\n\n";

print "Pattern as string:\n";
my $pattern = "\t|:%";
print "  Pattern: '$pattern'\n";
my @a1 = split $pattern, $line;
print "  Result: " . join(", ", @a1) . "\n";
print "  Count: " . scalar(@a1) . "\n\n";

print "Pattern as regex /\\t|:\\|%/:\n";
my @a2 = split /\t|:%/, $line;
print "  Result: " . join(", ", @a2) . "\n";
print "  Count: " . scalar(@a2) . "\n\n";

print "Pattern as character class /[\\t:%]/:\n";
my @a3 = split /[\t:%]/, $line;
print "  Result: " . join(", ", @a3) . "\n";
print "  Count: " . scalar(@a3) . "\n";
