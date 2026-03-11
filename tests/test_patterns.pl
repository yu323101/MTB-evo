#!/usr/bin/env perl
use warnings;

my $line = "a:b\tc%d";

print "Input: $line\n\n";

# Different regex patterns
print "Pattern 1: /\\t/ (tab only)\n";
my @a1 = split /\t/, $line;
print "  Result: " . join(", ", @a1) . "\n\n";

print "Pattern 2: /:/ (colon only)\n";
my @a2 = split /:/, $line;
print "  Result: " . join(", ", @a2) . "\n\n";

print "Pattern 3: /%/ (percent only)\n";
my @a3 = split /%/, $line;
print "  Result: " . join(", ", @a3) . "\n\n";

print "Pattern 4: /\\t|:|%/ (tab or colon or percent)\n";
my @a4 = split /\t|:%/, $line;
print "  Result: " . join(", ", @a4) . "\n\n";

print "Pattern 5: /[\\t:%]/ (character class)\n";
my @a5 = split /[\t:%]/, $line;
print "  Result: " . join(", ", @a5) . "\n";
