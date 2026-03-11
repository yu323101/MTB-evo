#!/usr/bin/env perl
use warnings;

my $line = "a|b|c";

print "String: $line\n\n";

print "Split by \"|\" (pipe as literal):\n";
my @a1 = split "|", $line;
print "  Parts: " . join(", ", @a1) . "\n";
print "  Count: " . scalar(@a1) . "\n\n";

print "Split by \"\\|\" (escaped pipe):\n";
my @a2 = split "\|", $line;
print "  Parts: " . join(", ", @a2) . "\n";
print "  Count: " . scalar(@a2) . "\n\n";

print "Split by /\\|/ (regex):\n";
my @a3 = split /\|/, $line;
print "  Parts: " . join(", ", @a3) . "\n";
print "  Count: " . scalar(@a3) . "\n";
