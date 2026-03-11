#!/usr/bin/env perl
use warnings;

# Read actual CNS file
open(my $fh, '<', '/Users/cosmos/Project/Allevo_script/test_data/raw/MD601.cns') or die $!;

my $count = 0;
while (my $line = <$fh>) {
    chomp $line;
    $count++;
    
    # Skip header
    next if $line =~ /^Chrom/;
    
    my @a = split "\t|:%", $line;
    
    print "Line $count:\n";
    print "  a[1] = '$a[1]'\n";
    
    # Check if this is position 1
    if ($a[1] == 1) {
        print "  *** Found position 1 ***\n";
        for (my $i = 0; $i <= 15 && $i <= $#a; $i++) {
            print "    a[$i] = '$a[$i]'\n";
        }
    }
    
    last if $count > 5;
}

close($fh);
