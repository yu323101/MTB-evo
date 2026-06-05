#!/usr/bin/env Rscript

# ============================================================================
# 变异分析图表生成脚本（R版本）
# 生成3张图表：Indel长度分布(07)、SNP替换类型(08)、变异功能分类(09)
# 使用中文标题，与01-06风格一致
# ============================================================================

suppressPackageStartupMessages({
  library(ggplot2)
  library(dplyr)
  library(tidyr)
  library(readr)
})

# 设置路径
SAMPLE <- "N24_1"
resolve_base_dir <- function() {
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  script_base <- NULL
  if (length(file_arg) > 0) {
    script_path <- normalizePath(sub("^--file=", "", file_arg[1]), mustWork = FALSE)
    script_base <- normalizePath(file.path(dirname(script_path), ".."), mustWork = FALSE)
  }
  default_base <- "/storeData/bjxkyy_data/lyw_62/test"
  if (!is.null(script_base) && dir.exists(script_base)) {
    return(script_base)
  }
  return(default_base)
}

BASE_DIR <- resolve_base_dir()
OUTDIR <- file.path(BASE_DIR, "figures")
VAR_DIR <- file.path(BASE_DIR, "variant_analysis")
dir.create(OUTDIR, recursive = TRUE, showWarnings = FALSE)
dir.create(VAR_DIR, recursive = TRUE, showWarnings = FALSE)

# Tableau 配色方案
TABLEAU_BLUE <- "#4E79A7"
TABLEAU_RED <- "#E15759"
TABLEAU_GRAY <- "#BAB0AC"

# 日志函数
LOG_FILE <- file.path(VAR_DIR, "variant_figures_r.log")
write_log <- function(msg) {
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  log_msg <- sprintf("[%s] %s", timestamp, msg)
  cat(log_msg, "\n")
  cat(log_msg, "\n", file = LOG_FILE, append = TRUE)
}

write_log("================================")
write_log("开始生成变异分析图表（R版本）")
write_log(sprintf("样本: %s", SAMPLE))
write_log("================================")

# 统一保存函数：同时输出 PNG + PDF
save_plot_dual <- function(plot_obj, filename_base, width, height, dpi = 300, outdir = OUTDIR) {
  png_file <- file.path(outdir, sprintf("%s.png", filename_base))
  pdf_file <- file.path(outdir, sprintf("%s.pdf", filename_base))
  ggsave(png_file, plot_obj, width = width, height = height, dpi = dpi)
  ggsave(pdf_file, plot_obj, width = width, height = height, device = "pdf")
  write_log(sprintf("✓ 已保存: %s", basename(png_file)))
  write_log(sprintf("✓ 已保存: %s", basename(pdf_file)))
}

# 读取CNS文件
read_cns <- function() {
  cns_file <- file.path(VAR_DIR, sprintf("%s.cns", SAMPLE))
  write_log(sprintf("读取CNS文件: %s", cns_file))
  
  # 读取数据
  cns_data <- read.table(cns_file, header = TRUE, sep = "\t", 
                         stringsAsFactors = FALSE, comment.char = "")
  
  # 筛选变异（SNP和Indel）
  variants <- cns_data %>%
    filter(grepl("^[ACGT]$", Var) | grepl("^[+-]", Var)) %>%
    mutate(
      is_indel = grepl("^[+-]", Var),
      indel_type = ifelse(is_indel, ifelse(grepl("^\\+", Var), "Insertion", "Deletion"), NA),
      indel_length = ifelse(is_indel, nchar(gsub("^[+-]", "", Var)), NA),
      signed_length = ifelse(is_indel, ifelse(indel_type == "Insertion", indel_length, -indel_length), NA)
    )
  
  return(variants)
}

# 读取注释文件
read_annotated <- function() {
  annot_file <- file.path(VAR_DIR, sprintf("%s_annotated.txt", SAMPLE))
  write_log(sprintf("读取注释文件: %s", annot_file))
  
  annot_data <- read.table(annot_file, header = FALSE, sep = "\t",
                          stringsAsFactors = FALSE, fill = TRUE, quote = "", comment.char = "")
  colnames(annot_data) <- c("Pos", "Ref", "Alt", "CodonPos", "MutType", "CodonChange", 
                           "GeneID", "GeneName", "Description", "Category")
  
  # 分类变异类型
  annot_data <- annot_data %>%
    mutate(
      VarType = case_when(
        MutType == "---" ~ "Intergenic",
        grepl("^Synonymous", MutType) ~ "Synonymous",
        grepl("^Nonsynonymous", MutType) ~ "Nonsynonymous",
        Alt %in% c("Insertion", "Deletion") ~ "Indel",
        TRUE ~ "Other"
      )
    )
  
  return(annot_data)
}

# 图07: Indel长度分布图
plot_07_indel_length <- function(variants) {
  write_log("步骤1: 生成Indel长度分布图(07)...")
  
  # 提取Indel
  indels <- variants %>%
    filter(is_indel == TRUE) %>%
    filter(abs(signed_length) <= 50)
  
  write_log(sprintf("  从.cns文件读取 %d 个Indel", nrow(indels)))
  
  # 统计长度分布
  length_dist <- indels %>%
    group_by(signed_length, indel_type) %>%
    summarise(Count = n(), .groups = "drop")
  
  min_len <- min(length_dist$signed_length)
  max_len <- max(length_dist$signed_length)
  write_log(sprintf("  长度范围: %d 到 +%d", min_len, max_len))
  
  # 绘制柱状图
  p <- ggplot(length_dist, aes(x = signed_length, y = Count, fill = indel_type)) +
    geom_bar(stat = "identity", color = "black", width = 0.8) +
    geom_text(aes(label = Count), vjust = -0.5, size = 3) +
    scale_fill_manual(values = c("Insertion" = TABLEAU_BLUE, "Deletion" = TABLEAU_RED)) +
    geom_vline(xintercept = 0, color = "black", linewidth = 0.5) +
    labs(title = "Indel Length Distribution",
         x = "Indel Length (bp)",
         y = "Count",
         fill = "Type") +
    theme_bw() +
    theme(plot.title = element_text(face = "bold", size = 16, hjust = 0.5),
          axis.title = element_text(size = 12),
          legend.position = "top")
  
  save_plot_dual(
    plot_obj = p,
    filename_base = sprintf("07_%s_indel_length_distribution", SAMPLE),
    width = 12,
    height = 6
  )
  write_log("✓ Indel长度分布图(07)保存完成")
}

# 图08: SNP替换类型分布
plot_08_snp_substitution <- function(variants) {
  write_log("步骤2: 生成SNP替换类型柱状图(08)...")
  
  # 提取SNP
  snps <- variants %>%
    filter(is_indel == FALSE)
  
  write_log(sprintf("  从.cns文件读取 %d 个SNP", nrow(snps)))
  
  # 统计替换类型
  snps <- snps %>%
    mutate(Substitution = paste0(Ref, ">", Var),
           MutClass = ifelse(Substitution %in% c("C>T", "T>C", "A>G", "G>A"), 
                            "Transition", "Transversion"))
  
  sub_counts <- snps %>%
    group_by(Substitution, MutClass) %>%
    summarise(Count = n(), .groups = "drop") %>%
    arrange(MutClass, desc(Count))
  
  write_log(sprintf("  共统计 %d 种替换类型", nrow(sub_counts)))
  
  # 绘制柱状图
  p <- ggplot(sub_counts, aes(x = Substitution, y = Count, fill = MutClass)) +
    geom_bar(stat = "identity", color = "black", width = 0.7) +
    geom_text(aes(label = Count), vjust = -0.5, size = 3) +
    scale_fill_manual(values = c("Transition" = TABLEAU_BLUE, "Transversion" = TABLEAU_RED)) +
    labs(title = "SNP Substitution Types",
         x = "Substitution Type",
         y = "Count",
         fill = "Mutation Type") +
    theme_bw() +
    theme(plot.title = element_text(face = "bold", size = 16, hjust = 0.5),
          axis.title = element_text(size = 12),
          axis.text.x = element_text(angle = 45, hjust = 1),
          legend.position = "top")
  
  save_plot_dual(
    plot_obj = p,
    filename_base = sprintf("08_%s_snp_substitution_barplot", SAMPLE),
    width = 10,
    height = 6
  )
  write_log("✓ SNP替换类型图(08)保存完成")
}

# 图09: 变异功能分类统计
plot_09_variant_classification <- function(annot_data) {
  write_log("步骤3: 生成功能分类环形图(09)...")
  
  write_log(sprintf("  共读取 %d 行注释数据", nrow(annot_data)))
  
  # 统计功能分类（不包括Indel）
  type_counts <- annot_data %>%
    filter(VarType != "Indel") %>%
    group_by(VarType) %>%
    summarise(Count = n(), .groups = "drop") %>%
    mutate(Percentage = Count / sum(Count) * 100,
           Label = sprintf("%s\n(%d)\n%.1f%%", VarType, Count, Percentage))
  
  write_log(sprintf("  Synonymous: %d (%.1f%%)", 
                   type_counts$Count[type_counts$VarType == "Synonymous"],
                   type_counts$Percentage[type_counts$VarType == "Synonymous"]))
  write_log(sprintf("  Nonsynonymous: %d (%.1f%%)", 
                   type_counts$Count[type_counts$VarType == "Nonsynonymous"],
                   type_counts$Percentage[type_counts$VarType == "Nonsynonymous"]))
  write_log(sprintf("  Intergenic: %d (%.1f%%)", 
                   type_counts$Count[type_counts$VarType == "Intergenic"],
                   type_counts$Percentage[type_counts$VarType == "Intergenic"]))
  
  # 绘制环形图
  p <- ggplot(type_counts, aes(x = "", y = Count, fill = VarType)) +
    geom_bar(stat = "identity", width = 1, color = "white", size = 0.5) +
    coord_polar(theta = "y") +
    scale_fill_manual(values = c("Synonymous" = TABLEAU_BLUE, 
                                "Nonsynonymous" = TABLEAU_RED, 
                                "Intergenic" = TABLEAU_GRAY)) +
    geom_text(aes(label = Label), position = position_stack(vjust = 0.5), 
              size = 3.5, color = "white", fontface = "bold") +
    labs(title = "Variant Functional Classification",
         fill = "Type") +
    theme_void() +
    theme(plot.title = element_text(face = "bold", size = 16, hjust = 0.5),
          legend.position = "right",
          legend.title = element_text(size = 12, face = "bold"),
          legend.text = element_text(size = 10))
  
  save_plot_dual(
    plot_obj = p,
    filename_base = sprintf("09_%s_variant_classification_donut", SAMPLE),
    width = 10,
    height = 6
  )
  write_log("✓ 功能分类图(09)保存完成")
}

# 主函数
main <- function() {
  # 读取数据
  variants <- read_cns()
  annot_data <- read_annotated()
  
  # 生成3张图表
  plot_07_indel_length(variants)
  plot_08_snp_substitution(variants)
  plot_09_variant_classification(annot_data)
  
  write_log("================================")
  write_log("所有图表生成完成")
  write_log("================================")
  write_log("生成文件:")
  write_log(sprintf("  - 07_%s_indel_length_distribution.png", SAMPLE))
  write_log(sprintf("  - 07_%s_indel_length_distribution.pdf", SAMPLE))
  write_log(sprintf("  - 08_%s_snp_substitution_barplot.png", SAMPLE))
  write_log(sprintf("  - 08_%s_snp_substitution_barplot.pdf", SAMPLE))
  write_log(sprintf("  - 09_%s_variant_classification_donut.png", SAMPLE))
  write_log(sprintf("  - 09_%s_variant_classification_donut.pdf", SAMPLE))
  write_log("================================")
}

# 执行主函数
main()
