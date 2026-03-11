#!/usr/bin/env perl
use warnings;

my $line = "a\tb:c%d";

print "String: $line\n\n";

print "split \"\\t|:\\|%%\" (original):\n";
my @a1 = split "\t|:%", $line;
print "  Result: " . join(", ", @a1) . "\n\n";

print "split /\\t|:\\|%/ (regex):\n";
my @a2 = split /\t|:%/, $line;
print "  Result: " . join(", ", @a2) . "\n\n";

print "split \"\\t\" (tab only):\n";
my @a3 = split "\t", $line;
print "  Result: " . join(", ", @a3) . "\n";
