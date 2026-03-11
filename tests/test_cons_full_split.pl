#!/usr/bin/env perl
use warnings;

my $cons = "T:20:6:13:65%:5E0";
print "Cons string: $cons\n\n";

print "split \"\\t|:\\|%%\" on cons:\n";
my @a = split "\t|:%", $cons;
print "  Parts: " . scalar(@a) . "\n";
for (my $i = 0; $i <= $#a; $i++) {
    print "  a[$i] = '$a[$i]'\n";
}
