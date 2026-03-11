#!/usr/bin/env perl
use warnings;

# Simulate actual CNS line
my $line = "gi|57116681|ref|NC_000962.2|\t1\tT\t.\tT:20:6:13:65%:5E0\tPass:0:0:0:0:1E0";

print "CNS line:\n$line\n\n";

print "split \"\\t|:\\|%%\" (original code):\n";
my @a = split "\t|:%", $line;
print "  Count: " . scalar(@a) . "\n";
for (my $i = 0; $i <= 10 && $i <= $#a; $i++) {
    print "  a[$i] = '$a[$i]'\n";
}

print "\nKey values for position 1:\n";
print "  a[1] (pos): $a[1]\n";
print "  a[2] (ref): $a[2]\n";
print "  a[3] (var): $a[3]\n";
print "  a[4] (cons info): $a[4]\n";
print "  a[5] (pass info): $a[5]\n";

# Now split the cons info column
print "\nSplitting cons info column (a[4]='$a[4]'):\n";
my @cons = split /:/, $a[4];
print "  Cons parts: " . join(", ", @cons) . "\n";
print "  cons=$cons[0], cov=$cons[1], reads1=$cons[2], reads2=$cons[3], freq=$cons[4]\n";
