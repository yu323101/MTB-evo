#!/usr/bin/env perl
use warnings;

# Create a test with just position 46644
my $loci_file = '/tmp/test_loci.txt';
my $depth_file = '/Users/cosmos/Project/Allevo_script/test_data/input/depth.txt';
my $cns_file = '/Users/cosmos/Project/Allevo_script/test_data/raw/MD601.cns';

# Create loci file with just 46644
open(my $f, '>', $loci_file) or die $!;
print $f "46644\n";
close($f);

# Run the recall script
system("perl /Users/cosmos/Project/Allevo_script/test_data/code/1st_loci_recall_cns.pl $loci_file $depth_file $cns_file > /tmp/test_output.fas");

# Show output
print "Output:\n";
open(my $out, '<', '/tmp/test_output.fas') or die $!;
while (my $line = <$out>) {
    print $line;
}
close($out);
