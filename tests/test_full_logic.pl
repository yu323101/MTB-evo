#!/usr/bin/env perl
use warnings;

# Simulate the original Perl script logic for position 46644
my $loci_file = '/Users/cosmos/Project/Allevo_script/test_data/input/diff_location.list';
my $depth_file = '/Users/cosmos/Project/Allevo_script/test_data/input/depth.txt';
my $cns_file = '/Users/cosmos/Project/Allevo_script/test_data/raw/MD601.cns';

# Read loci
my %hash;
my @list;
open(my $f1, '<', $loci_file) or die $!;
while (my $line = <$f1>) {
    chomp $line;
    $hash{$line} = "N";
    push @list, $line;
}
close($f1);

# Read depth
my $dep;
open(my $f2, '<', $depth_file) or die $!;
while (my $line = <$f2>) {
    chomp $line;
    $dep = $line * 0.1;
}
close($f2);

print "Depth threshold: $dep\n\n";

# Process CNS
open(my $f3, '<', $cns_file) or die $!;
while (my $line = <$f3>) {
    chomp $line;
    
    my @a = split "\t|:%", $line;
    
    # Check if this is position 46644
    if ($a[1] == 46644) {
        print "Processing position 46644:\n";
        print "  a[0] = '$a[0]'\n";
        print "  a[1] = '$a[1]' (position)\n";
        print "  a[2] = '$a[2]' (ref)\n";
        print "  a[3] = '$a[3]' (var)\n";
        print "  a[4] = '$a[4]'\n";
        print "  a[5] = '$a[5]'\n";
        print "  a[6] = '$a[6]'\n";
        print "  a[7] = '$a[7]'\n";
        print "  a[8] = '$a[8]'\n";
        
        # Check conditions
        print "\nCondition checks:\n";
        print "  a[0] ne 'Chrom': " . ($a[0] ne 'Chrom' ? 'true' : 'false') . "\n";
        print "  exists hash{a[1]}: " . (exists $hash{$a[1]} ? 'true' : 'false') . "\n";
        print "  length(a[3]) == 1: " . (length($a[3]) == 1 ? 'true' : 'false') . " (length=" . length($a[3]) . ")\n";
        print "  a[8] ne '-': " . ($a[8] ne '-' ? 'true' : 'false') . " (a[8]='$a[8]')\n";
        print "  a[5] > $dep: " . ($a[5] > $dep ? 'true' : 'false') . " (a[5]='$a[5]')\n";
        print "  a[5] >= 3: " . ($a[5] >= 3 ? 'true' : 'false') . "\n";
        
        last;
    }
}
close($f3);
