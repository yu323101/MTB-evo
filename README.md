# MTB-Evo: 结核杆菌进化分析工具包

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**面向预防医学和基础医学研究人员的友好型生物信息学工具**

---

## 🎯 适用人群

- 预防医学研究人员
- 基础医学研究人员
- 公共卫生专业人员
- **无需编程基础**，只需按步骤操作即可

## 📋 系统要求

- **操作系统**: Linux 或 macOS
- **内存**: 建议 16GB 以上
- **磁盘空间**: 根据样本数量，建议预留 100GB
- **网络**: 安装时需要联网下载依赖

## 🚀 快速开始（3步完成）

### 第一步：安装（5分钟）

```bash
# 1. 下载工具包
git clone <repository-url>
cd mtb-evo

# 2. 运行安装脚本
bash install.sh
```

安装过程中会自动完成：
- ✅ 创建 conda 环境
- ✅ 安装所有依赖工具
- ✅ 下载参考数据库
- ✅ 验证安装

### 第二步：准备数据

将你的双端测序数据（fastq.gz 文件）放在工作目录中。

**文件命名格式**（重要！）：
```
样本A: SampleA_1.fastq.gz, SampleA_2.fastq.gz
样本B: SampleB_1.fastq.gz, SampleB_2.fastq.gz
样本C: SampleC_1.fastq.gz, SampleC_2.fastq.gz
```

**创建样本列表**：
```bash
# 自动生成样本列表
ls *_1.fastq.gz | sed 's/_1.fastq.gz//' > samples.txt
```

### 第三步：运行分析

```bash
# 激活环境
conda activate mtb-evo

# 运行完整流程
mtb-evo run-all --samples samples.txt --output-dir results/
```

## 📂 分析结果

分析完成后，结果保存在 `results/` 目录：

| 文件 | 说明 | 用途 |
|------|------|------|
| `all_strains.fadel-InvMisF5.bak.fa` | 核心 SNP 序列 | 构建系统发育树 |
| `pair.txt` | 样本间 SNP 距离矩阵 | 传播链分析 |
| `test.tree` | 系统发育树 | 进化关系可视化 |

## 📖 详细使用指南

### 方式一：一键运行（推荐）

适合大多数用户，自动完成所有步骤：

```bash
mtb-evo run-all --samples samples.txt --output-dir results/
```

### 方式二：分步运行（高级）

如果你想控制每一步，或某一步出错需要重跑：

```bash
# Step 1: 生成分析脚本
mtb-evo step1 --samples samples.txt --output-dir results/

# Step 2: SNP calling（耗时最长，建议后台运行）
cd results
nohup bash pair_end.sh > pair_end.log 2>&1 &

# 查看进度
tail -f pair_end.log

# Step 2 完成后，继续后续步骤
mtb-evo step3-10 --output-dir results/
```

### 方式三：Snakemake 流程（批量处理）

适合批量处理多个项目：

```bash
# 编辑配置文件
vim config.yaml

# 运行流程
snakemake --cores 4
```

## 🔧 单命令使用

### Step 4: 提取差异位点

```bash
mtb-evo diff-loci --snp-dir . --output diff_location.list
```

**输入**: `*.snp` 文件  
**输出**: `diff_location.list`（差异位点坐标列表）

### Step 7: 基因型回溯

```bash
mtb-evo recall \
    --loci diff_location.list \
    --depth depth.txt \
    --cns sample.cns \
    --output sample.fas
```

**输入**: 差异位点列表、深度阈值、CNS 文件  
**输出**: `*.fas`（基因型序列）

### Step 8: 合并序列

```bash
mtb-evo merge --fas-dir . --output all_strains.fa
```

**输入**: `*.fas` 文件  
**输出**: `all_strains.fa`（合并后的多序列比对）

### Step 9: 提取祖先碱基

```bash
mtb-evo wild-extract \
    --loci diff_location.list \
    --ancestor tb.ancestor.fasta \
    --output wild_loci.list
```

**输入**: 差异位点列表、祖先序列  
**输出**: `wild_loci.list`（野生型碱基列表）

### Step 10: 核心 SNP 过滤

```bash
mtb-evo filter \
    --wild-loci wild_loci.list \
    --alignment all_strains.fa \
    --threshold 5 \
    --output-prefix all_strains
```

**输入**: 野生型碱基列表、序列比对、阈值  
**输出**: 
- `all_strains.fadel-InvMisF5.bak.fa`（过滤后的核心 SNP）
- `all_strains.fadel-InvMisF5.bak.loc`（保留位点坐标）

## ❓ 常见问题

### Q1: 安装失败怎么办？

**检查清单**：
1. 网络连接是否正常
2. 是否有足够的磁盘空间（至少 10GB）
3. conda 是否正确安装

**解决方法**：
```bash
# 手动创建环境
conda env create -f environment.yml
conda activate mtb-evo
pip install -e .
bash scripts/download_varscan.sh
```

### Q2: Step 2 运行时间多长？

取决于样本数量和服务器性能：
- 6 个样本：约 2-4 小时
- 20 个样本：约 8-12 小时

**建议**：使用 `nohup` 或集群提交，避免中断。

### Q3: 如何知道 Step 2 是否完成？

```bash
# 查看日志
tail -f results/pair_end.log

# 检查输出文件
ls results/*.snp | wc -l  # 应该等于样本数
```

### Q4: 结果文件看不懂？

- **核心 SNP 序列** (`*.bak.fa`): 用于构建系统发育树
- **距离矩阵** (`pair.txt`): 样本间的 SNP 差异数
- **系统发育树** (`test.tree`): 进化关系，可用 FigTree 或 iTOL 可视化

### Q5: 报错 "No .snp files found"

**原因**: Step 2 未完成或失败

**解决**:
```bash
# 检查日志
cat results/pair_end.log | grep -i error

# 如果失败，重跑 Step 2
cd results && bash pair_end.sh
```

## 🛠️ 故障排除

### 错误 1: "VarScan not found"

```bash
# 解决：下载 VarScan
bash scripts/download_varscan.sh
```

### 错误 2: "command not found: mtb-evo"

```bash
# 解决：激活环境
conda activate mtb-evo

# 验证
which mtb-evo
```

### 错误 3: "Out of memory"

**原因**: 内存不足

**解决**:
- 减少并行任务数
- 在高内存服务器上运行
- 使用集群提交

## 📚 示例数据

我们提供了示例数据集，用于测试安装和学习使用：

```bash
# 复制示例数据到工作目录
cp -r test_data/* ./

# 运行示例
mtb-evo run-all --samples samples.txt --output-dir results/
```

示例数据包含 6 个样本，运行时间约 10 分钟（不含 Step 2）。

## 📝 引用

如果本工具对你的研究有帮助，请引用：

```
MTB-Evo: A user-friendly pipeline for Mycobacterium tuberculosis 
evolutionary analysis. 2024. GitHub: https://github.com/.../mtb-evo
```

## 💡 技术支持

- **问题反馈**: [GitHub Issues](https://github.com/.../mtb-evo/issues)
- **邮件咨询**: support@mtb-evo.org
- **在线文档**: https://mtb-evo.readthedocs.io

## 📜 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**祝使用愉快！如有问题，欢迎反馈。**
