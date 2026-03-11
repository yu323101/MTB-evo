#!/usr/bin/env perl
use warnings;

# Exact copy of original script with debug

my %hash;
my @list;

open F1, '/tmp/test_loci.txt' or die $!;
while(<F1>){
chomp;
$hash{$_}="N";
push @list, $_;
}
close F1;

open F2, '/Users/cosmos/Project/Allevo_script/test_data/input/depth.txt' or die $!;
my $dep;
while(<F2>){
chomp;
$dep=$_*0.1;
}
close F2;

print "Depth threshold: $dep\n";
print "Loci: @list\n\n";

open F3, '/Users/cosmos/Project/Allevo_script/test_data/raw/MD601.cns' or die $!;
while(<F3>){
chomp;
my @a=split "\t|:%",$_;
if($a[0] ne "Chrom" && exists $hash{$a[1]}){
print "Found position $a[1]\n";
print "  a[0] = '$a[0]'\n";
print "  a[1] = '$a[1]'\n";
print "  a[2] = '$a[2]'\n";
print "  a[3] = '$a[3]'\n";
print "  a[4] = '$a[4]'\n";
print "  a[5] = '$a[5]'\n";
print "  a[6] = '$a[6]'\n";
print "  a[7] = '$a[7]'\n";
print "  a[8] = '$a[8]'\n";

my $l=length $a[3];
print "\nLength of a[3]: $l\n";

if($l==1){
print "Passed: length == 1\n";

if($a[8] ne "-"){
print "Passed: a[8] != '-'\n";

print "Checking: a[5]='$a[5]' > $dep\n";
if($a[5] > $dep && $a[5] >= 3){
print "Passed: depth check\n";

if($a[5]=~m/[0-9]+/ && $a[6]=~m/[0-9]+/ && $a[7]=~m/[0-9]+/){
print "Passed: all are numbers\n";

my $real=($a[6]+$a[7])/$a[5];
print "Real ratio: $real\n";

if($real>0.8){
print "Passed: real > 0.8\n";

if($a[8] >= 75){
$hash{$a[1]}=$a[3];
print "Result: mutation ($a[3])\n";
}elsif($a[8] <= 25){
$hash{$a[1]}=$a[2];
print "Result: wild type ($a[2])\n";
}else{
$hash{$a[1]}="?";
print "Result: mixed\n";
}
}else{
print "Failed: real <= 0.8\n";
$hash{$a[1]}="N";
}
}else{
print "Failed: not all are numbers\n";
$hash{$a[1]}="N";
}
}else{
print "Failed: depth check\n";
$hash{$a[1]}="N";
}
}else{
print "Failed: a[8] == '-'\n";
$hash{$a[1]}="N";
}
}else{
print "Failed: length != 1\n";
$hash{$a[1]}="N";
}

last;
}
}
close F3;

print "\nFinal result: $hash{46644}\n";
