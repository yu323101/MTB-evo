#!/usr/bin/env perl
use warnings;

# Read actual CNS file and show split results for position 46644
open(my $fh, '<', '/Users/cosmos/Project/Allevo_script/test_data/raw/MD601.cns') or die $!;

while (my $line = <$fh>) {
    chomp $line;
    
    # Skip header
    next if $line =~ /^Chrom/;
    
    my @a = split "\t|:%", $line;
    
    # Check if this is position 46644
    if ($a[1] == 46644) {
        print "Position 46644:\n";
        print "  Total parts: " . scalar(@a) . "\n";
        for (my $i = 0; $i <= 15 && $i <= $#a; $i++) {
            print "  a[$i] = '$a[$i]'\n";
        }
        
        print "\nKey indices:\n";
        print "  a[1] (pos): $a[1]\n";
        print "  a[2] (ref): $a[2]\n";
        print "  a[3] (var): $a[3]\n";
        print "  a[4] (cons): $a[4]\n";
        print "  a[5] (cov): $a[5]\n";
        print "  a[6] (reads1): $a[6]\n";
        print "  a[7] (reads2): $a[7]\n";
        print "  a[8] (freq): $a[8]\n";
        
        last;
    }
}

close($fh);
