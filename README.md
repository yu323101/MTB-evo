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

# 方式一：一键运行（推荐）
mtb-evo run-all --samples samples.txt --output-dir results/

# 方式二：分步运行（见下方详细指南）
# 适合需要自定义参数或排查问题的用户
```

**性能优化提示**：
- 默认使用 50% CPU 核心（如 48 核服务器使用 24 线程）
- 可自定义线程数：`--threads 32 --sort-threads 16`
- 自动检测并创建 bowtie2 索引（首次运行）

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

#### Step 1-2: SNP Calling（变异检测）

```bash
# 生成 SNP calling 脚本
# 默认使用 50% CPU 核心，可自定义：--threads 32 --sort-threads 16
python3 scripts/pair_fixed_nostrandbias.py local_test/samples.txt

# 执行脚本（后台运行，耗时最长）
cd results
nohup bash pair_end.sh > pair_end.log 2>&1 &

# 查看进度
tail -f pair_end.log
```

**输出文件**：
- `*.snp` - SNP 检测结果
- `*.cns` - 一致性序列
- `*.sort.bam` - 排序后的比对文件

#### Step 3: 提取差异位点

```bash
cd results
mtb-evo diff-loci --snp-dir . --output diff_loci.txt
```

**输出**：`diff_loci.txt`（差异位点列表）

#### Step 4: 基因型召回

```bash
# 使用默认深度 10（无需创建 depth.txt）
mtb-evo recall \
    --loci diff_loci.txt \
    --cns MD601.cleaned.cns \
    --output MD601.recall.fasta

mtb-evo recall \
    --loci diff_loci.txt \
    --cns MD602.cleaned.cns \
    --output MD602.recall.fasta

# 或使用自定义深度文件
echo 15 > depth.txt
mtb-evo recall --loci diff_loci.txt --depth depth.txt --cns sample.cns --output sample.recall.fasta
```

**输出**：`*.recall.fasta`（基因型序列）

#### Step 5: 合并序列

```bash
mtb-evo merge --fas-dir . --output merged.fasta
```

**输出**：`merged.fasta`（合并后的多序列比对）

#### Step 6: 提取野生型碱基

```bash
mtb-evo wild-extract \
    --loci diff_loci.txt \
    --ancestor ../data/tb.ancestor.fasta \
    --output wildtype.fasta
```

**输出**：`wildtype.fasta`（野生型碱基序列）

#### Step 7: 核心 SNP 过滤

```bash
mtb-evo filter \
    --wild-loci wildtype.fasta \
    --alignment merged.fasta \
    --threshold 5 \
    --output-prefix core_snps
```

**输出**：
- `all_strains.fadel-InvMisF5.bak.fa`（过滤后的核心 SNP）
- `all_strains.fadel-InvMisF5.bak.loc`（保留位点坐标）

#### Step 8: SNP 距离计算

```bash
mtb-evo distance \
    --alignment all_strains.fadel-InvMisF5.bak.fa \
    --output distance_matrix.txt
```

**输出**：`distance_matrix.txt`（样本间 SNP 距离矩阵）

### 方式三：Snakemake 流程（批量处理）

适合批量处理多个项目：

```bash
# 编辑配置文件
vim config.yaml

# 运行流程
snakemake --cores 4
```

---

## 📊 实际运行案例

以下是在 48 核服务器上运行 2 个样本（MD601 和 MD602）的完整示例：

### 系统配置
- **CPU**: Intel Xeon Silver 4214 × 2 (48 核)
- **内存**: 32GB
- **线程设置**: 24 线程（默认 50%）

### 运行结果

| 步骤 | 命令 | 结果 | 耗时 |
|------|------|------|------|
| Step 1-2 | SNP calling | 1423 SNPs (MD601), 1400 SNPs (MD602) | ~2 小时 |
| Step 3 | diff-loci | 224 差异位点 / 1348 总位点 | <1 分钟 |
| Step 4 | recall | 2 个样本基因型召回成功 | <1 分钟 |
| Step 5 | merge | 2 个文件合并成功 | <1 分钟 |
| Step 6 | wild-extract | 224 个野生型碱基提取 | <1 分钟 |
| Step 7 | filter | 201/224 位点保留 | <1 分钟 |
| Step 8 | distance | 距离矩阵计算成功 | <1 分钟 |

### 完整命令流

```bash
# 1. 环境准备
conda activate mtb-evocd /home/nmx/mtb-evo

# 2. SNP Calling（使用 24 线程）
python3 scripts/pair_fixed_nostrandbias.py local_test/samples.txt
cd results && nohup bash pair_end.sh > pair_end.log 2>&1 &

# 3. 等待 Step 2 完成后，继续后续步骤
cd /home/nmx/mtb-evo/results

# Step 3: 差异位点提取
mtb-evo diff-loci --snp-dir . --output diff_loci.txt

# Step 4: 基因型召回（使用默认深度 10）
mtb-evo recall -l diff_loci.txt -c MD601.cleaned.cns -o MD601.recall.fasta
mtb-evo recall -l diff_loci.txt -c MD602.cleaned.cns -o MD602.recall.fasta

# Step 5: 序列合并
mtb-evo merge -f . -o merged.fasta

# Step 6: 野生型提取
mtb-evo wild-extract -l diff_loci.txt -a ../data/tb.ancestor.fasta -o wildtype.fasta

# Step 7: 核心 SNP 过滤
mtb-evo filter -w wildtype.fasta -a merged.fasta -o core_snps

# Step 8: 距离计算
mtb-evo distance -a all_strains.fadel-InvMisF5.bak.fa -o distance_matrix.txt
```

### 输出文件清单

```
results/
├── MD601.cleaned.snp              # SNP 结果
├── MD601.cleaned.cns              # CNS 文件
├── MD602.cleaned.snp
├── MD602.cleaned.cns
├── diff_loci.txt                  # 224 差异位点
├── depth.txt                      # 深度阈值
├── MD601.recall.fasta             # 基因型召回
├── MD602.recall.fasta
├── merged.fasta                   # 合并序列
├── wildtype.fasta                 # 野生型碱基
├── all_strains.fadel-InvMisF5.bak.fa    # 核心 SNP
├── all_strains.fadel-InvMisF5.bak.loc   # 坐标信息
└── distance_matrix.txt            # 距离矩阵
```

## 🔧 单命令使用

### Step 4: 提取差异位点

```bash
mtb-evo diff-loci --snp-dir . --output diff_location.list
```

**输入**: `*.snp` 文件  
**输出**: `diff_location.list`（差异位点坐标列表）

### Step 4: 基因型召回

```bash
# 使用默认深度 10（无需创建 depth.txt）
mtb-evo recall \
    --loci diff_loci.txt \
    --cns sample.cns \
    --output sample.recall.fasta

# 或使用自定义深度文件
echo 15 > depth.txt
mtb-evo recall --loci diff_loci.txt --depth depth.txt --cns sample.cns --output sample.recall.fasta
```

**输入**: 差异位点列表、CNS 文件（可选：深度阈值文件）  
**输出**: `*.recall.fasta`（基因型序列）  
**默认深度**: 10（如果未提供 depth.txt）

### Step 5: 合并序列

```bash
mtb-evo merge --fas-dir . --output merged.fasta
```

**输入**: `*.fas` 或 `*.fasta` 文件（自动识别两种格式）  
**输出**: `merged.fasta`（合并后的多序列比对）

### Step 6: 提取野生型碱基

```bash
mtb-evo wild-extract \
    --loci diff_loci.txt \
    --ancestor ../data/tb.ancestor.fasta \
    --output wildtype.fasta
```

**输入**: 差异位点列表、祖先序列  
**输出**: `wildtype.fasta`（野生型碱基序列）

### Step 7: 核心 SNP 过滤

```bash
mtb-evo filter \
    --wild-loci wildtype.fasta \
    --alignment merged.fasta \
    --threshold 5 \
    --output-prefix core_snps
```

**输入**: 野生型碱基序列、合并的序列比对、阈值  
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

**原因**: Step 2 未完成或失败；或输出文件不在 results/ 目录

**解决**:
```bash
# 检查日志
cat results/pair_end.log | grep -i error

# 检查输出文件位置
ls results/*.snp
ls test_data/*.snp  # 如果在这里，需要移动到 results/

# 如果失败，重跑 Step 2
cd results && bash pair_end.sh
```

### Q6: 如何自定义线程数？

**解决**:
```bash
# 使用 --threads 和 --sort-threads 参数
python3 scripts/pair_fixed_nostrandbias.py samples.txt --threads 32 --sort-threads 16

# 默认使用 50% CPU 核心
# 例如 48 核服务器默认使用 24 线程
```

## 🛠️ 故障排除

### 错误 1: Git 操作超时或失败

**症状**: `git pull`、`git fetch` 或 `git clone` 超时

**原因**: 网络防火墙限制 HTTPS 连接

**解决方法**:
```bash
# 方法 1: 增加 Git 超时时间
git config --global http.lowSpeedLimit 1000
git config --global http.lowSpeedTime 300

# 方法 2: 使用 wget/curl 下载单个文件（跳过证书验证）
curl -k -o scripts/pair_fixed_nostrandbias.py \
  https://raw.githubusercontent.com/yu323101/mtb-evo/main/scripts/pair_fixed_nostrandbias.py

# 方法 3: 手动复制文件
# 从其他设备下载后，通过 U 盘、邮件等方式传输到服务器
```

### 错误 2: "VarScan not found"

```bash
# 解决：下载 VarScan
bash scripts/download_varscan.sh
```

### 错误 3: "No .fas or .fasta files found"

**原因**: merge 命令找不到输入文件

**解决**:
```bash
# 确保文件扩展名正确（支持 .fas 和 .fasta）
ls *.fas *.fasta 2>/dev/null

# 如果文件是 .fasta 格式，直接运行即可
mtb-evo merge --fas-dir . --output merged.fasta
```

### 错误 4: "command not found: mtb-evo"

```bash
# 解决：激活环境
conda activate mtb-evo

# 验证
which mtb-evo
```

### 错误 5: "Out of memory"

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

示例数据包含多个样本，运行时间约 10 分钟（不含 Step 2）。

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
