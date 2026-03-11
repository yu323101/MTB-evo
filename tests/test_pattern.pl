#!/usr/bin/env perl
use warnings;

# Check what "\t|:%" actually means
my $pattern = "\t|:%";
print "Pattern: '$pattern'\n";
print "Length: " . length($pattern) . "\n";
print "Characters:\n";
for (my $i = 0; $i < length($pattern); $i++) {
    my $char = substr($pattern, $i, 1);
    print "  [$i] = '$char' (ord=" . ord($char) . ")\n";
}

print "\nTesting split:\n";
my $line = "a|b:c\td%e";
my @a = split $pattern, $line;
print "  Input: $line\n";
print "  Result: " . join(", ", @a) . "\n";
