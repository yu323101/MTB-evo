#!/usr/bin/env perl
use warnings;

my $cns_file = '/Users/cosmos/Project/Allevo_script/test_data/raw/MD601.cns';

open(my $fh, '<', $cns_file) or die $!;
while (my $line = <$fh>) {
    chomp $line;
    next if $line =~ /^Chrom/;
    
    my @a = split "\t|:%", $line;
    
    if ($a[1] == 46644) {
        print "Position 46644:\n";
        print "  a[5] = '$a[5]'\n";
        print "  a[6] = '$a[6]'\n";
        print "  a[7] = '$a[7]'\n";
        print "  a[8] = '$a[8]'\n";
        
        # Check if a[5] is numeric
        if ($a[5] =~ /^[0-9]+$/) {
            print "  a[5] is numeric: YES\n";
        } else {
            print "  a[5] is numeric: NO\n";
        }
        
        last;
    }
}
close($fh);
