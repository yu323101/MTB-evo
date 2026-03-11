#!/usr/bin/env perl
use warnings;

# Check if "\t|:%" exists in CNS file
open(my $fh, '<', '/Users/cosmos/Project/Allevo_script/test_data/raw/MD601.cns') or die $!;

my $found = 0;
while (my $line = <$fh>) {
    if ($line =~ /\t|:%/) {
        print "Found \"\\t|:%\" in line: $line\n";
        $found = 1;
        last;
    }
}

if (!$found) {
    print "No \"\\t|:%\" found in CNS file\n";
    print "This means split \"\\t|:%\" behaves like split \"\\t\"\n";
}

close($fh);
