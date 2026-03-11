#!/usr/bin/perl
use strict;
use warnings;

# 读取位置文件
open my $F1, '<', $ARGV[0] or die "无法打开位置文件: $!";
my @list;
while (<$F1>) {
    chomp;
    push @list, $_;
}
close $F1;

# 读取序列文件
open my $F2, '<', $ARGV[1] or die "无法打开序列文件: $!";
my $seq = '';
while (<$F2>) {
    chomp;
    next if /^>/; # 跳过FASTA注释行
    $seq .= $_;
}
close $F2;

# 输出每个位点的碱基，如果超出长度则输出N
my $length = length($seq);
foreach my $i (@list) {
    my $base;
    if ($i > 0 && $i <= $length) {
        $base = substr($seq, $i - 1, 1);
    } else {
        $base = 'N'; # 超出序列范围，填充N
    }
    print "$i\t$base\n";
}

