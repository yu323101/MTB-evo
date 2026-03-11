#!/usr/bin/env perl
use warnings;

my $line = "gi|57116681|ref|NC_000962.2|\t46644\tA\t.\tA:675:675:0:0%:1E0\tPass:0:0:0:0:1E0";

print "Line: $line\n\n";

print "split \"\\t|:\\|%%\":\n";
my @a = split "\t|:%", $line;
print "  Count: " . scalar(@a) . "\n";
for (my $i = 0; $i <= 8; $i++) {
    print "  a[$i] = '$a[$i]'\n";
}

print "\nNote: a[5] should be cov (675), but we see '$a[5]'\n";
