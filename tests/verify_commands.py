#!/usr/bin/env python3
"""验证所有命令的测试脚本"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, '/Users/cosmos/Project/Allevo_script/mtb_evo/src')

def test_diff_loci():
    """测试 Step 4: diff_loci"""
    print("=" * 60)
    print("测试 Step 4: diff_loci")
    print("=" * 60)
    
    from mtb_evo.commands.diff_loci import extract_diff_loci
    
    test_data_dir = Path("/Users/cosmos/Project/Allevo_script/test_data")
    snp_dir = test_data_dir / "output_expected"
    output_file = Path("/tmp/test_diff_loci_output.list")
    expected_file = test_data_dir / "input" / "diff_location.list"
    
    try:
        extract_diff_loci(snp_dir, output_file)
        
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
        return False

def test_merge():
    """测试 Step 8: merge"""
    print("\n" + "=" * 60)
    print("测试 Step 8: merge")
    print("=" * 60)
    
    from mtb_evo.commands.merge import merge_fas
    
    test_data_dir = Path("/Users/cosmos/Project/Allevo_script/test_data")
    fas_dir = test_data_dir / "output_expected"
    output_file = Path("/tmp/test_merge_output.fa")
    
    try:
        merge_fas(fas_dir, output_file)
        
        # 检查输出
        with open(output_file) as f:
            content = f.read()
        
        # 应该包含所有样本
        samples = ["MD601", "MD602", "MD603", "MD604", "MD605", "MD606"]
        found_samples = []
        for sample in samples:
            if f">{sample}" in content:
                found_samples.append(sample)
        
        if len(found_samples) == len(samples):
            print(f"✅ Step 8 (merge): 通过 (合并了 {len(found_samples)} 个样本)")
            return True
        else:
            print(f"❌ Step 8 (merge): 只找到 {len(found_samples)}/{len(samples)} 个样本")
            return False
    except Exception as e:
        print(f"❌ Step 8 (merge): 错误 - {e}")
        return False

def test_wild_extract():
    """测试 Step 9: wild_extract"""
    print("\n" + "=" * 60)
    print("测试 Step 9: wild_extract")
    print("=" * 60)
    
    from mtb_evo.commands.wild_extract import extract_wild_loci
    
    test_data_dir = Path("/Users/cosmos/Project/Allevo_script/test_data")
    loci_file = test_data_dir / "input" / "diff_location.list"
    ancestor_file = test_data_dir / "ref" / "tb.ancestor.fasta"
    output_file = Path("/tmp/test_wild_extract_output.list")
    expected_file = test_data_dir / "input" / "wild_loci.list"
    
    try:
        extract_wild_loci(loci_file, ancestor_file, output_file)
        
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
            # 显示前5行差异
            actual_lines = actual.splitlines()
            expected_lines = expected.splitlines()
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

def test_filter():
    """测试 Step 10: filter"""
    print("\n" + "=" * 60)
    print("测试 Step 10: filter")
    print("=" * 60)
    
    from mtb_evo.commands.filter import filter_core_snp
    
    test_data_dir = Path("/Users/cosmos/Project/Allevo_script/test_data")
    
    # 注意：需要创建 all_strains.fa 输入文件
    # 使用 merge 的输出
    fas_dir = test_data_dir / "output_expected"
    alignment_file = Path("/tmp/test_filter_input.fa")
    
    # 先合并
    from mtb_evo.commands.merge import merge_fas
    merge_fas(fas_dir, alignment_file)
    
    wild_loci_file = test_data_dir / "input" / "wild_loci.list"
    output_prefix = "/tmp/test_filter_output"
    expected_fa = test_data_dir / "output_expected" / "all_strains.fadel-InvMisF5.bak.fa"
    expected_loc = test_data_dir / "output_expected" / "all_strains.fadel-InvMisF5.bak.loc"
    
    try:
        filter_core_snp(wild_loci_file, alignment_file, 5, output_prefix)
        
        # 对比输出
        output_fa = f"{output_prefix}.fadel-InvMisF5.bak.fa"
        output_loc = f"{output_prefix}.fadel-InvMisF5.bak.loc"
        
        with open(output_fa) as f:
            actual_fa = f.read()
        with open(expected_fa) as f:
            expected_fa_content = f.read()
        
        with open(output_loc) as f:
            actual_loc = f.read()
        with open(expected_loc) as f:
            expected_loc_content = f.read()
        
        fa_match = actual_fa == expected_fa_content
        loc_match = actual_loc == expected_loc_content
        
        if fa_match and loc_match:
            print("✅ Step 10 (filter): 通过")
            return True
        else:
            if not fa_match:
                print("❌ Step 10 (filter): FASTA 输出不匹配")
            if not loc_match:
                print("❌ Step 10 (filter): LOC 输出不匹配")
            return False
    except Exception as e:
        print(f"❌ Step 10 (filter): 错误 - {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 60)
    print("MTB-Evo 命令验证测试")
    print("=" * 60 + "\n")
    
    results = []
    
    results.append(("Step 4: diff_loci", test_diff_loci()))
    results.append(("Step 8: merge", test_merge()))
    results.append(("Step 9: wild_extract", test_wild_extract()))
    results.append(("Step 10: filter", test_filter()))
    
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
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
