#!/usr/bin/env python3
"""简化版验证脚本（不依赖typer）"""

import sys
from pathlib import Path
from collections import defaultdict

def test_diff_loci():
    """测试 Step 4: diff_loci"""
    print("=" * 60)
    print("测试 Step 4: diff_loci")
    print("=" * 60)
    
    test_data_dir = Path("/Users/cosmos/Project/Allevo_script/test_data")
    snp_dir = test_data_dir / "output_expected"
    output_file = Path("/tmp/test_diff_loci_output.list")
    expected_file = test_data_dir / "input" / "diff_location.list"
    
    try:
        # 实现逻辑
        snp_files = list(snp_dir.glob("*.snp"))
        total_samples = len(snp_files)
        print(f"找到 {total_samples} 个 SNP 文件")
        
        locus_count = defaultdict(int)
        for snp_file in snp_files:
            seen_in_this_sample = set()
            with open(snp_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    cols = line.split()
                    if len(cols) >= 1:
                        try:
                            pos = int(cols[0])
                            if pos not in seen_in_this_sample:
                                locus_count[pos] += 1
                                seen_in_this_sample.add(pos)
                        except ValueError:
                            continue
        
        diff_loci = [pos for pos, count in locus_count.items() if count < total_samples]
        
        with open(output_file, "w") as f:
            for pos in sorted(diff_loci):
                f.write(f"{pos}\n")
        
        # 对比输出
        with open(output_file) as f:
            actual = f.read()
        with open(expected_file) as f:
            expected = f.read()
        
        if actual == expected:
            print("✅ Step 4 (diff_loci): 通过")
            return True
        else:
            print("❌ Step 4 (diff_loci): 输出不匹配")
            print(f"  实际行数: {len(actual.splitlines())}")
            print(f"  预期行数: {len(expected.splitlines())}")
            return False
    except Exception as e:
        print(f"❌ Step 4 (diff_loci): 错误 - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_wild_extract():
    """测试 Step 9: wild_extract"""
    print("\n" + "=" * 60)
    print("测试 Step 9: wild_extract")
    print("=" * 60)
    
    test_data_dir = Path("/Users/cosmos/Project/Allevo_script/test_data")
    loci_file = test_data_dir / "input" / "diff_location.list"
    ancestor_file = test_data_dir / "ref" / "tb.ancestor.fasta"
    output_file = Path("/tmp/test_wild_extract_output.list")
    expected_file = test_data_dir / "input" / "wild_loci.list"
    
    try:
        # 读取位点
        loci = []
        with open(loci_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    loci.append(int(line))
        
        print(f"读取了 {len(loci)} 个位点")
        
        # 读取祖先序列
        seq = ""
        with open(ancestor_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith(">"):
                    continue
                seq += line
        
        print(f"祖先序列长度: {len(seq)} bp")
        
        # 提取碱基
        with open(output_file, "w") as f:
            for pos in loci:
                if 1 <= pos <= len(seq):
                    base = seq[pos - 1]
                else:
                    base = "N"
                f.write(f"{pos}\t{base}\n")
        
        # 对比输出
        with open(output_file) as f:
            actual = f.read()
        with open(expected_file) as f:
            expected = f.read()
        
        if actual == expected:
            print("✅ Step 9 (wild_extract): 通过")
            return True
        else:
            print("❌ Step 9 (wild_extract): 输出不匹配")
            actual_lines = actual.splitlines()
            expected_lines = expected.splitlines()
            print(f"  实际行数: {len(actual_lines)}")
            print(f"  预期行数: {len(expected_lines)}")
            for i, (a, e) in enumerate(zip(actual_lines[:5], expected_lines[:5])):
                if a != e:
                    print(f"  第{i+1}行不同:")
                    print(f"    实际: {a}")
                    print(f"    预期: {e}")
            return False
    except Exception as e:
        print(f"❌ Step 9 (wild_extract): 错误 - {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 60)
    print("MTB-Evo 核心逻辑验证")
    print("=" * 60 + "\n")
    
    results = []
    
    results.append(("Step 4: diff_loci", test_diff_loci()))
    results.append(("Step 9: wild_extract", test_wild_extract()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 核心逻辑验证通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
