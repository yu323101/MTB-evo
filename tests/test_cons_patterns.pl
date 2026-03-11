#!/usr/bin/env perl
use warnings;

my $cons = "A:675:675:0:0%:1E0";
print "Cons string: $cons\n\n";

print "Testing different split patterns:\n\n";

print "1. split /:/ (colon only):\n";
my @a1 = split /:/, $cons;
print "   Parts: " . scalar(@a1) . "\n";
print "   Result: " . join(", ", @a1) . "\n\n";

print "2. split /%/ (percent only):\n";
my @a2 = split /%/, $cons;
print "   Parts: " . scalar(@a2) . "\n";
print "   Result: " . join(", ", @a2) . "\n\n";

print "3. split /:|%/ (colon or percent):\n";
my @a3 = split /:|%/, $cons;
print "   Parts: " . scalar(@a3) . "\n";
print "   Result: " . join(", ", @a3) . "\n\n";

print "4. split \"\\t|:\\|%%\" (original):\n";
my @a4 = split "\t|:%", $cons;
print "   Parts: " . scalar(@a4) . "\n";
print "   Result: " . join(", ", @a4) . "\n";
