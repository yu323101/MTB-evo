#!/usr/bin/env perl
use warnings;

my $cons = "T:20:6:13:65%:5E0";
print "Cons string: $cons\n";

print "\nsplit /:/ (colon only):\n";
my @a1 = split /:/, $cons;
print "  Result: " . join(", ", @a1) . "\n";

print "\nsplit \"\\t|:\\|%%\" on cons only:\n";
my @a2 = split "\t|:%", $cons;
print "  Result: " . join(", ", @a2) . "\n";
