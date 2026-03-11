#!/usr/bin/env perl
use warnings;

my $dep = 1;
my $a5 = "Pass:0:0:0:0:1E0";
my $a6 = "1";
my $a7 = "0";
my $a8 = "0";

print "Testing conditions:\n";
print "  a[5] = '$a5'\n";
print "  a[6] = '$a6'\n";
print "  a[7] = '$a7'\n";
print "  a[8] = '$a8'\n\n";

print "  a[5] > $dep: " . ($a5 > $dep ? 'true' : 'false') . "\n";
print "  a[5] >= 3: " . ($a5 >= 3 ? 'true' : 'false') . "\n";
print "  a[5] =~ /[0-9]+/: " . ($a5 =~ m/[0-9]+/ ? 'true' : 'false') . "\n";
print "  a[6] =~ /[0-9]+/: " . ($a6 =~ m/[0-9]+/ ? 'true' : 'false') . "\n";
print "  a[7] =~ /[0-9]+/: " . ($a7 =~ m/[0-9]+/ ? 'true' : 'false') . "\n";

# Check numeric comparison
print "\nNumeric context:\n";
print "  0+$a5 = " . (0+$a5) . "\n";
print "  0+$a6 = " . (0+$a6) . "\n";
print "  0+$a7 = " . (0+$a7) . "\n";
print "  0+$a8 = " . (0+$a8) . "\n";
