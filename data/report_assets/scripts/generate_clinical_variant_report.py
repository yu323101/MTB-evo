#!/usr/bin/env python3
"""
生成临床变异检测报告（表2）
基于.cns文件和annotated.txt
"""

import pandas as pd
import os
from datetime import datetime

# 设置路径
SAMPLE = "N24_1"
BASE_DIR = "/storeData/bjxkyy_data/lyw_62/test"
TABLE_DIR = os.path.join(BASE_DIR, "table")
ANNOT_FILE = os.path.join(BASE_DIR, "variant_analysis", f"{SAMPLE}_annotated.txt")
CNS_FILE = os.path.join(BASE_DIR, "variant_analysis", f"{SAMPLE}.cns")

def read_annotated():
    """读取注释文件"""
    data = []
    with open(ANNOT_FILE, 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            data.append(parts)
    return data

def read_cns():
    """读取cns文件"""
    snp_count = 0
    indel_count = 0
    
    with open(CNS_FILE, 'r') as f:
        header = f.readline()
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 4:
                var = parts[3]
                if var in ['A', 'C', 'G', 'T']:
                    snp_count += 1
                elif var.startswith('+') or var.startswith('-'):
                    indel_count += 1
    
    return snp_count, indel_count

def classify_mutation_type(annot_data):
    """分类变异类型"""
    synonymous = 0
    nonsynonymous = 0
    intergenic = 0
    indel = 0
    
    for row in annot_data:
        if len(row) >= 5:
            type_col = row[4]
            if type_col == "---":
                intergenic += 1
            elif type_col.startswith("Synonymous"):
                synonymous += 1
            elif type_col.startswith("Nonsynonymous"):
                nonsynonymous += 1
            elif type_col in ["Insertion", "Deletion"]:
                indel += 1
    
    return synonymous, nonsynonymous, intergenic, indel

def main():
    print("=" * 50)
    print("生成临床变异检测报告")
    print(f"样本: {SAMPLE}")
    print("=" * 50)
    
    # 读取数据
    print("\n步骤1: 读取变异数据...")
    annot_data = read_annotated()
    snp_count, indel_count = read_cns()
    
    total_variants = snp_count + indel_count
    print(f"  SNP: {snp_count}")
    print(f"  Indel: {indel_count}")
    print(f"  总变异数: {total_variants}")
    
    # 分类统计
    print("\n步骤2: 统计变异类型...")
    synonymous, nonsynonymous, intergenic, indel_annot = classify_mutation_type(annot_data)
    
    # 注意：annotated.txt中SNP被合并后可能数量减少
    total_annotated = synonymous + nonsynonymous + intergenic
    
    print(f"  同义突变: {synonymous}")
    print(f"  非同义突变: {nonsynonymous}")
    print(f"  基因间区: {intergenic}")
    print(f"  Indel: {indel_annot}")
    print(f"  注释总计: {total_annotated}")
    
    # 计算百分比
    syn_pct = synonymous / total_annotated * 100 if total_annotated > 0 else 0
    nonsyn_pct = nonsynonymous / total_annotated * 100 if total_annotated > 0 else 0
    inter_pct = intergenic / total_annotated * 100 if total_annotated > 0 else 0
    
    snp_pct = snp_count / total_variants * 100 if total_variants > 0 else 0
    indel_pct = indel_count / total_variants * 100 if total_variants > 0 else 0
    
    # 创建报告数据
    print("\n步骤3: 生成报告...")
    
    report_data = [
        ["总变异数", total_variants, "100%", "-", "/"],
        ["同义突变", synonymous, f"{syn_pct:.1f}%", "不改变氨基酸 通常无临床意义", "低"],
        ["非同义突变", nonsynonymous, f"{nonsyn_pct:.1f}%", "改变氨基酸 可能影响蛋白功能", "高"],
        ["基因间区变异", intergenic, f"{inter_pct:.1f}%", "非编码区 通常无临床意义", "低"],
        ["点突变(SNP)", snp_count, f"{snp_pct:.1f}%", "常见变异类型", "中"],
        ["插入缺失(Indel)", indel_count, f"{indel_pct:.1f}%", "可能影响较大", "高"],
    ]
    
    # 创建DataFrame
    df = pd.DataFrame(report_data, columns=[
        "变异类型", "数量", "占比", "临床意义", "建议关注程度"
    ])
    
    # 保存为CSV
    output_file = os.path.join(TABLE_DIR, f"临床变异检测报告_{SAMPLE}.csv")
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n✓ 报告已保存: {output_file}")
    print(f"\n报告内容:")
    print(df.to_string(index=False))
    
    print("\n" + "=" * 50)
    print("临床变异检测报告生成完成")
    print("=" * 50)

if __name__ == "__main__":
    main()
