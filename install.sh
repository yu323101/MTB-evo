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

# shellcheck disable=SC1091
source "$SCRIPT_DIR/src/scripts/install_helpers.sh"

# 检查conda
echo "🔍 检查conda..."
if ! discover_conda; then
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
    echo "环境 mtb-evo 已存在，执行依赖更新..."
    conda env update -n mtb-evo -f environment.yml
    echo "✓ 环境依赖更新完成"
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

# 兜底确保关键 Python 包可用（避免旧环境未刷新导致缺包）
if ! python -c "import matplotlib, pandas" > /dev/null 2>&1; then
    echo "⚠️  matplotlib/pandas 未检测到，执行补装..."
    pip install matplotlib pandas > /dev/null 2>&1
fi

echo "✓ Python包安装成功"
echo ""

# 检查关键 R 依赖
echo "🔍 检查R依赖..."
if command -v Rscript > /dev/null 2>&1; then
    if Rscript -e "library(ggplot2); library(jsonlite); library(dplyr); library(tidyr); library(readr); library(scales)" > /dev/null 2>&1; then
        echo "✓ R图表依赖可用"
    else
        echo "✗ 错误：R图表依赖缺失，请重新执行 conda env update -n mtb-evo -f environment.yml"
        exit 1
    fi
else
    echo "✗ 错误：未找到 Rscript"
    exit 1
fi
echo ""

# 下载VarScan
echo "⬇️  下载VarScan..."
bash src/scripts/download_varscan.sh
echo ""

# 检查安装
echo "🔍 验证安装..."
if command -v mtb-evo > /dev/null 2>&1; then
    echo "✓ mtb-evo命令可用"
    mtb-evo --help | head -5
else
    echo "✗ 错误：mtb-evo命令不可用"
    exit 1
fi

if command -v snakemake > /dev/null 2>&1; then
    echo "✓ snakemake命令可用"
    snakemake --help | head -5
else
    echo "✗ 错误：snakemake命令不可用"
    exit 1
fi
echo ""

if command -v fastp > /dev/null 2>&1; then
    echo "✓ fastp命令可用"
    fastp --version | head -1
else
    echo "✗ 错误：fastp命令不可用"
    exit 1
fi
echo ""

# 复制参考数据
echo "📂 设置参考数据..."
if [ ! -d "data" ]; then
    mkdir -p data
fi

# 检查参考基因组是否存在
if [ ! -f "data/tb.ancestor.fasta" ]; then
    echo "⚠️  警告：默认参考序列 data/tb.ancestor.fasta 不存在"
    echo "   请从服务器复制（当前默认 profile=tb_ancestor）"
fi

if [ ! -f "data/tb_h37rv.fasta" ]; then
    echo "⚠️  提示：可选参考序列 data/tb_h37rv.fasta 不存在"
    echo "   如需切换 profile=tb_h37rv，请补充该文件"
fi

echo ""
echo "=========================================="
echo "  ✅ 安装完成！"
echo "=========================================="
echo ""
echo "使用方法："
echo "  1. 激活环境：conda activate mtb-evo"
echo "  2. 查看帮助：mtb-evo --help"
echo "  3. Snakemake全流程：snakemake --snakefile Snakefile --configfile config/config.yaml -j 4 all"
echo ""
echo "详细文档：README.md"
echo ""
