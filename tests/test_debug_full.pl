#!/usr/bin/env perl
use warnings;

# Full simulation with debug
my $loci_file = '/tmp/test_loci.txt';
my $depth_file = '/Users/cosmos/Project/Allevo_script/test_data/input/depth.txt';
my $cns_file = '/Users/cosmos/Project/Allevo_script/test_data/raw/MD601.cns';

# Create loci file
open(my $f, '>', $loci_file) or die $!;
print $f "46644\n";
close($f);

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

print "Depth threshold: $dep\n";
print "Loci: @list\n\n";

# Process CNS
open(my $f3, '<', $cns_file) or die $!;
while (my $line = <$f3>) {
    chomp $line;
    
    my @a = split "\t|:%", $line;
    
    if ($a[1] == 46644) {
        print "Found position 46644\n";
        print "Line: $line\n";
        print "Split result:\n";
        for (my $i = 0; $i <= 10 && $i <= $#a; $i++) {
            print "  a[$i] = '$a[$i]'\n";
        }
        
        # Apply logic
        if ($a[0] ne "Chrom" && exists $hash{$a[1]}) {
            print "\nPassed initial checks\n";
            
            my $l = length $a[3];
            print "Length of a[3] (var): $l\n";
            
            if ($l == 1) {
                print "Passed: length == 1\n";
                
                if ($a[8] ne "-") {
                    print "Passed: a[8] != '-' (a[8]='$a[8]')\n";
                    
                    print "Checking: a[5]='$a[5]' > $dep\n";
                    if ($a[5] > $dep && $a[5] >= 3) {
                        print "Passed: depth check\n";
                        
                        if ($a[5] =~ m/[0-9]+/ && $a[6] =~ m/[0-9]+/ && $a[7] =~ m/[0-9]+/) {
                            print "Passed: all are numbers\n";
                            
                            my $real = ($a[6] + $a[7]) / $a[5];
                            print "Real ratio: $real\n";
                            
                            if ($real > 0.8) {
                                print "Passed: real > 0.8\n";
                                
                                print "Freq: a[8]='$a[8]'\n";
                                if ($a[8] >= 75) {
                                    $hash{$a[1]} = $a[3];
                                    print "Result: mutation (a[3]='$a[3]')\n";
                                } elsif ($a[8] <= 25) {
                                    $hash{$a[1]} = $a[2];
                                    print "Result: wild type (a[2]='$a[2]')\n";
                                } else {
                                    $hash{$a[1]} = "?";
                                    print "Result: mixed\n";
                                }
                            } else {
                                print "Failed: real <= 0.8\n";
                            }
                        } else {
                            print "Failed: not all are numbers\n";
                        }
                    } else {
                        print "Failed: depth check (a[5]='$a[5]')\n";
                    }
                } else {
                    print "Failed: a[8] == '-'\n";
                }
            } else {
                print "Failed: length != 1\n";
            }
        }
        
        last;
    }
}
close($f3);

print "\nFinal result: $hash{46644}\n";
