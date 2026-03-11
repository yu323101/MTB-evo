#!/usr/bin/env perl
use warnings;

my %hash;
my @list;

my $loci_file = '/tmp/test_loci.txt';
my $depth_file = '/Users/cosmos/Project/Allevo_script/test_data/input/depth.txt';
my $cns_file = '/Users/cosmos/Project/Allevo_script/test_data/raw/MD601.cns';

open F1, $loci_file or die $!;
while(<F1>){
chomp;
$hash{$_}="N";
push @list, $_;
}
close F1;

open F2, $depth_file or die $!;
while(<F2>){
chomp;
$dep=$_*0.1;
}
close F2;

open F3, $cns_file or die $!;
while(<F3>){
chomp;
@a=split "\t|:%",$_;
if($a[0] ne "Chrom" && exists $hash{$a[1]}){
$l=length $a[3];
if($l==1){
if($a[8] ne "-"){
if($a[5] > $dep && $a[5] >= 3){
if($a[5]=~m/[0-9]+/ && $a[6]=~m/[0-9]+/ && $a[7]=~m/[0-9]+/){
$real=($a[6]+$a[7])/$a[5];
if($real>0.8){
if($a[8] >= 75){
$hash{$a[1]}=$a[3];
}elsif($a[8] <= 25){
$hash{$a[1]}=$a[2];
}elsif($a[8]>25 && $a[8]<75){
$hash{$a[1]}="?";
}
}else{
$hash{$a[1]}="N";
}
}else{
$hash{$a[1]}="N";
}
}else{
$hash{$a[1]}="N";
}
}else{
$hash{$a[1]}="N";
}
}else{
$hash{$a[1]}="N";
}
}else{
$hash{$a[1]}="N";
}
}
}
close F3;

$name="MD601";
print ">$name\n";
foreach $i (@list){
print "$hash{$i}";
}
print "\n";
