#!/bin/bash
# MTB-Evo Installation Script

set -e

echo "=========================================="
echo "  MTB-Evo 安装脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查conda
echo "🔍 检查conda..."
if ! command -v conda > /dev/null 2>&1; then
    echo "✗ 错误：未找到conda"
    echo "请先安装Anaconda或Miniconda:"
    echo "  https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi
echo "✓ conda已安装"
echo ""

# 创建conda环境
echo "📦 创建conda环境..."
if conda env list | grep -q "^mtb-evo"; then
    echo "环境 mtb-evo 已存在，跳过创建"
else
    conda env create -f environment.yml
    echo "✓ 环境创建成功"
fi
echo ""

# 激活环境
echo "🔄 激活环境..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate mtb-evo
echo "✓ 环境已激活"
echo ""

# 安装Python包
echo "📥 安装Python包..."
pip install -e . > /dev/null 2>&1
echo "✓ Python包安装成功"
echo ""

# 下载VarScan
echo "⬇️  下载VarScan..."
bash src/scripts/download_varscan.sh
echo ""

# 检查安装
echo "🔍 验证安装..."
if command -v mtb-evo > /dev/null 2>&1; then
    echo "✓ mtb-evo命令可用"
    mtb-vo --help | head -5
else
    echo "✗ 错误：mtb-evo命令不可用"
    exit 1
fi
echo ""

# 复制参考数据
echo "📂 设置参考数据..."
if [ ! -d "data" ]; then
    mkdir -p data
fi

# 检查参考基因组是否存在
if [ ! -f "data/tb_h37rv.fasta" ]; then
    echo "⚠️  警告：参考基因组 data/tb_h37rv.fasta 不存在"
    echo "   请从服务器复制或从NCBI下载"
fi

if [ ! -f "data/tb.ancestor.fasta" ]; then
    echo "⚠️  警告：祖先序列 data/tb.ancestor.fasta 不存在"
    echo "   请从服务器复制"
fi

echo ""
echo "=========================================="
echo "  ✅ 安装完成！"
echo "=========================================="
echo ""
echo "使用方法："
echo "  1. 激活环境：conda activate mtb-evo"
echo "  2. 查看帮助：mtb-evo --help"
echo "  3. 运行示例：bash run_example.sh"
echo ""
echo "详细文档：README.md"
echo ""
