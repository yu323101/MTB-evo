#!/usr/bin/env python3
"""
生成样本级变异信息表（表3）
基于.cns文件，包含SNP和Indel
"""

import pandas as pd
import os
import re
from datetime import datetime

# 设置路径
SAMPLE = "N24_1"
BASE_DIR = "/storeData/bjxkyy_data/lyw_62/test"
TABLE_DIR = os.path.join(BASE_DIR, "table")
VAR_DIR = os.path.join(BASE_DIR, "variant_analysis")
DRUG_DB = "/home/zcd/script/zcd_drug_snp/Total_drug_resistance_mutation.txt"

CNS_FILE = os.path.join(VAR_DIR, f"{SAMPLE}.cns")
ANNOT_FILE = os.path.join(VAR_DIR, f"{SAMPLE}_annotated.txt")

# 氨基酸映射
AA_MAP = {
    'A': 'Alanine', 'Ala': 'Alanine',
    'R': 'Arginine', 'Arg': 'Arginine',
    'N': 'Asparagine', 'Asn': 'Asparagine',
    'D': 'Aspartic acid', 'Asp': 'Aspartic acid',
    'C': 'Cysteine', 'Cys': 'Cysteine',
    'E': 'Glutamic acid', 'Glu': 'Glutamic acid',
    'Q': 'Glutamine', 'Gln': 'Glutamine',
    'G': 'Glycine', 'Gly': 'Glycine',
    'H': 'Histidine', 'His': 'Histidine',
    'I': 'Isoleucine', 'Ile': 'Isoleucine',
    'L': 'Leucine', 'Leu': 'Leucine', 'LeT': 'Leucine',
    'K': 'Lysine', 'Lys': 'Lysine',
    'M': 'Methionine', 'Met': 'Methionine',
    'F': 'Phenylalanine', 'Phe': 'Phenylalanine',
    'P': 'Proline', 'Pro': 'Proline',
    'S': 'Serine', 'Ser': 'Serine',
    'T': 'Threonine', 'Thr': 'Threonine',
    'W': 'Tryptophan', 'Trp': 'Tryptophan',
    'Y': 'Tyrosine', 'Tyr': 'Tyrosine',
    'V': 'Valine', 'Val': 'Valine',
    '*': 'Stop', 'stop': 'Stop'
}

# 药物分类
DRUG_CLASS = {
    'ISONIAZID': '一线药物',
    'RIFAMPICIN': '一线药物',
    'PYRAZINAMIDE': '一线药物',
    'ETHAMBUTOL': '一线药物',
    'STREPTOMYCIN': '一线药物',
    'FLUOROQUINOLONES': '二线药物',
    'ETHIONAMIDE': '二线药物',
    'PARA-AMINOSALISYLIC_ACID': '二线药物',
    'CAPREOMYCIN': '二线药物',
    'KANAMYCIN': '二线药物',
    'AMIKACIN': '二线药物',
    'CLOFAZIMINE': '二线药物',
    'BEDAQUILINE': '二线药物',
    'LINEZOLID': '二线药物'
}

def convert_aa(aa_code):
    """转换氨基酸缩写为全称"""
    return AA_MAP.get(aa_code, aa_code)

def convert_drug_class(drug_name):
    """转换药物为分类"""
    return DRUG_CLASS.get(drug_name, '其他')

def read_cns():
    """读取cns文件，只返回SNP和Indel（过滤掉参考位点）"""
    variants = []
    with open(CNS_FILE, 'r') as f:
        header = f.readline().strip().split('\t')
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 10:
                var = parts[3]
                # 只保留SNP（单个碱基）和Indel（以+或-开头）
                if var in ['A', 'C', 'G', 'T'] or var.startswith('+') or var.startswith('-'):
                    variants.append({
                        'Chrom': parts[0],
                        'Position': int(parts[1]),
                        'Ref': parts[2],
                        'Var': var,
                        'Cons': parts[4],
                        'StrandFilter': parts[5],
                        'SamplesRef': parts[6],
                        'SamplesHet': parts[7],
                        'SamplesHom': parts[8],
                        'SamplesNC': parts[9]
                    })
    return variants

def parse_consensus(cons_str):
    """解析consensus字符串"""
    # 格式: Cons:Cov:Reads1:Reads2:Freq:P-value
    parts = cons_str.split(':')
    if len(parts) >= 5:
        return {
            'cons': parts[0],
            'depth': int(parts[1]),
            'reads1': int(parts[2]),
            'reads2': int(parts[3]),
            'freq': parts[4]
        }
    return None

def read_annotated():
    """读取注释文件，创建位置到注释的映射"""
    annot_map = {}
    with open(ANNOT_FILE, 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 10:
                pos = parts[0]
                # 处理范围位置（如"3847237-3847238"）
                if '-' in pos:
                    pos = pos.split('-')[0]
                
                annot_map[int(pos)] = {
                    'pos': parts[0],
                    'ref': parts[1],
                    'alt': parts[2],
                    'codon_pos': parts[3],
                    'mut_type': parts[4],
                    'codon_change': parts[5],
                    'gene_id': parts[6],
                    'gene_name': parts[7],
                    'description': parts[8],
                    'category': parts[9]
                }
    return annot_map

def read_drug_db():
    """读取耐药数据库"""
    drug_map = {}
    try:
        with open(DRUG_DB, 'r') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    # 格式: gene_name\tposition\tdrug
                    gene = parts[0]
                    pos = parts[1]
                    drug = parts[2]
                    key = f"{gene}_{pos}"
                    drug_map[key] = drug
    except FileNotFoundError:
        print(f"警告: 耐药数据库文件未找到: {DRUG_DB}")
    return drug_map

def determine_genotype(samples_hom, samples_het):
    """判断基因型"""
    if samples_hom == "1":
        return "Hom"
    elif samples_het == "1":
        return "Het"
    else:
        return "Unknown"

def parse_mutation_type(mut_type_str):
    """解析突变类型"""
    if mut_type_str == "---":
        return "Intergenic", "-", "-"
    elif mut_type_str.startswith("Synonymous"):
        return "Synonymous", mut_type_str, mut_type_str
    elif mut_type_str.startswith("Nonsynonymous"):
        return "Nonsynonymous", mut_type_str, mut_type_str
    elif mut_type_str in ["Insertion", "Deletion"]:
        return mut_type_str, "-", "-"
    else:
        return "Other", mut_type_str, mut_type_str

def main():
    print("=" * 60)
    print("生成样本级变异信息表")
    print(f"样本: {SAMPLE}")
    print("=" * 60)
    
    # 读取数据
    print("\n步骤1: 读取变异数据...")
    variants = read_cns()
    print(f"  从.cns文件读取 {len(variants)} 个变异")
    
    print("\n步骤2: 读取注释信息...")
    annot_map = read_annotated()
    print(f"  读取 {len(annot_map)} 条注释")
    
    print("\n步骤3: 读取耐药数据库...")
    drug_map = read_drug_db()
    print(f"  读取 {len(drug_map)} 条耐药记录")
    
    # 处理每个变异
    print("\n步骤4: 处理变异信息...")
    rows = []
    
    for var in variants:
        pos = var['Position']
        ref = var['Ref']
        alt = var['Var']
        
        # 创建ID
        var_id = f"{pos}_{ref}/{alt}"
        
        # 解析consensus信息
        cons_info = parse_consensus(var['Cons'])
        depth = cons_info['depth'] if cons_info else 0
        var_reads = cons_info['reads2'] if cons_info else 0
        freq_str = cons_info['freq'] if cons_info else "0%"
        
        # 判断基因型
        genotype = determine_genotype(var['SamplesHom'], var['SamplesHet'])
        
        # 判断是否为Indel
        is_indel = alt.startswith('+') or alt.startswith('-')
        
        # 获取注释信息
        annot = annot_map.get(pos, {})
        
        # 处理耐药信息
        drug_mutation = "-"
        drug_info = "-"
        gene_name = annot.get('gene_name', '-')
        
        if gene_name != '-' and not is_indel:
            # 检查耐药数据库
            drug_key = f"{gene_name}_{pos}"
            if drug_key in drug_map:
                drug = drug_map[drug_key]
                drug_mutation = drug
                drug_info = convert_drug_class(drug)
        
        # 解析突变类型
        mut_type_str = annot.get('mut_type', '-')
        var_type, aa_change, codon_info = parse_mutation_type(mut_type_str)
        
        # 提取密码子位置和氨基酸变化
        codon_pos = annot.get('codon_pos', '-')
        codon_change = annot.get('codon_change', '-')
        
        # 处理氨基酸全称
        if aa_change != "-" and "-" in aa_change:
            parts = aa_change.split('-')
            if len(parts) >= 3:
                mut_type_name = parts[0]
                aa1 = parts[1].split('/')[0] if '/' in parts[1] else parts[1]
                aa2 = parts[2].split('/')[0] if '/' in parts[2] else parts[2]
                aa_change_full = f"{convert_aa(aa1)}-{convert_aa(aa2)}"
            else:
                aa_change_full = aa_change
        else:
            aa_change_full = aa_change
        
        # 创建行数据
        row = {
            'ID': var_id,
            '基因组位置': pos,
            '参考碱基': ref,
            '变异碱基': alt,
            '频率': freq_str,
            '测序深度': depth,
            '支持变异reads数': var_reads,
            '基因型': genotype,
            '耐药突变': drug_mutation,
            '耐药信息': drug_info,
            '基因标签': annot.get('gene_id', '-'),
            '基因名': gene_name,
            '基因位置': '-',  # 需要从注释计算
            '密码子位置': codon_pos,
            '密码子变化': codon_change,
            '氨基酸变化': aa_change_full,
            '变异类型': var_type,
            '基因功能': annot.get('description', '-'),
            '功能分类': annot.get('category', '-')
        }
        
        rows.append(row)
    
    print(f"  处理完成，共 {len(rows)} 个变异")
    
    # 创建DataFrame
    print("\n步骤5: 生成表格...")
    df = pd.DataFrame(rows)
    
    # 定义列顺序（19个字段）
    columns = [
        'ID', '基因组位置', '参考碱基', '变异碱基', '频率', '测序深度', 
        '支持变异reads数', '基因型', '耐药突变', '耐药信息', '基因标签', 
        '基因名', '基因位置', '密码子位置', '密码子变化', '氨基酸变化', 
        '变异类型', '基因功能', '功能分类'
    ]
    
    df = df[columns]
    
    # 保存为CSV
    output_file = os.path.join(TABLE_DIR, f"样本级变异信息表_{SAMPLE}.csv")
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n✓ 表格已保存: {output_file}")
    print(f"  总行数: {len(df)}")
    print(f"  总列数: {len(df.columns)}")
    
    # 统计信息
    print(f"\n统计信息:")
    print(f"  SNP: {len(df[df['变异碱基'].isin(['A', 'C', 'G', 'T'])])}")
    print(f"  Indel: {len(df[~df['变异碱基'].isin(['A', 'C', 'G', 'T'])])}")
    print(f"  同义突变: {len(df[df['变异类型'] == 'Synonymous'])}")
    print(f"  非同义突变: {len(df[df['变异类型'] == 'Nonsynonymous'])}")
    print(f"  基因间区: {len(df[df['变异类型'] == 'Intergenic'])}")
    
    print("\n" + "=" * 60)
    print("样本级变异信息表生成完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
