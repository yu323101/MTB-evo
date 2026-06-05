#!/usr/bin/env Rscript

# ============================================================================
# QC 图表统一生成脚本
# 生成6张标准化QC图，使用Tableau配色方案
# ============================================================================

suppressPackageStartupMessages({
  library(ggplot2)
  library(jsonlite)
  library(dplyr)
  library(tidyr)
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
OUTDIR <- file.path(BASE_DIR, "qc_figures")
FIGURES_DIR <- file.path(BASE_DIR, "figures")
FASTP_DIR <- file.path(BASE_DIR, "fastp_qc")
ALIGN_DIR <- file.path(BASE_DIR, "alignment_qc")
dir.create(OUTDIR, recursive = TRUE, showWarnings = FALSE)
dir.create(FIGURES_DIR, recursive = TRUE, showWarnings = FALSE)

# Tableau 配色方案
TABLEAU_COLORS <- list(
  blue = "#4E79A7",
  red = "#E15759",
  green = "#59A14F",
  orange = "#F28E2B",
  gray = "#BAB0AC"
)

# 日志函数
LOG_FILE <- file.path(OUTDIR, "qc_generation.log")
write_log <- function(msg) {
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  log_msg <- sprintf("[%s] %s", timestamp, msg)
  cat(log_msg, "\n")
  cat(log_msg, "\n", file = LOG_FILE, append = TRUE)
}

write_log("================================")
write_log("开始生成统一QC图表")
write_log(sprintf("样本: %s", SAMPLE))
write_log("================================")

# 统一保存函数：同时输出 PNG + PDF，可同时保存到多个目录
save_plot_dual <- function(plot_obj, filename_base, width, height, dpi = 300, outdirs = c(OUTDIR, FIGURES_DIR)) {
  for (dir in outdirs) {
    png_file <- file.path(dir, sprintf("%s.png", filename_base))
    pdf_file <- file.path(dir, sprintf("%s.pdf", filename_base))
    ggsave(png_file, plot_obj, width = width, height = height, dpi = dpi)
    ggsave(pdf_file, plot_obj, width = width, height = height, device = "pdf")
    write_log(sprintf("✓ 已保存: %s", basename(png_file)))
    write_log(sprintf("✓ 已保存: %s", basename(pdf_file)))
  }
}

# 图1-2: 碱基组成分布图
generate_base_composition <- function(read_num) {
  write_log(sprintf("生成碱基组成分布图 (R%d)...", read_num))
  
  # 读取fastp JSON
  fastp_file <- file.path(FASTP_DIR, sprintf("N24_1_%d_fastp.json", read_num))
  fastp_data <- fromJSON(fastp_file)
  
  # 提取content curves (before filtering)
  content <- fastp_data$read1_before_filtering$content_curves
  
  # 创建数据框 (使用比例 0-1，参考 fastqc_plot.R)
  df <- data.frame(
    Cycle = 1:151,
    A = content$A[1:151],
    T = content$T[1:151],
    C = content$C[1:151],
    G = content$G[1:151]
  ) %>%
    pivot_longer(cols = -Cycle, names_to = "Base", values_to = "Proportion")
  
  # 绘制 (参考 fastqc_plot.R 样式)
  p <- ggplot(df, aes(x = Cycle, y = Proportion, color = Base)) +
    geom_line(linewidth = 1) +
    scale_color_brewer(palette = "Set1") +  # fastqc_plot.R 默认配色
    scale_y_continuous(labels = scales::percent_format()) +  # 百分比格式
    labs(title = sprintf("Base Composition (R%d)", read_num),
         x = "Position in read (bp)",
         y = "Base proportion",
         color = "Base") +
    theme_bw() +
    theme(plot.title = element_text(face = "bold", size = 16, hjust = 0.5),
          axis.title = element_text(size = 12),
          legend.position = "bottom")
  
  save_plot_dual(
    plot_obj = p,
    filename_base = sprintf("0%d_base_composition_R%d", read_num, read_num),
    width = 10,
    height = 6
  )
}

# 图3-4: 测序质量分布图
generate_quality_distribution <- function(read_num) {
  write_log(sprintf("生成测序质量分布图 (R%d)...", read_num))
  
  # 读取fastp JSON
  fastp_file <- file.path(FASTP_DIR, sprintf("N24_1_%d_fastp.json", read_num))
  fastp_data <- fromJSON(fastp_file)
  
  # 提取quality curves (before filtering)
  quality_curves <- fastp_data$read1_before_filtering$quality_curves
  
  # 创建数据框 (参考 fastqc_plot.R，包含 Mean, Q10, Q90)
  quality_df <- data.frame(
    Cycle = 1:151,
    Mean = quality_curves$mean[1:151]
  )
  
  # 计算 Q10 和 Q90 (基于各碱基质量)
  quality_df$Q10 <- sapply(1:151, function(i) {
    scores <- c(quality_curves$A[i], quality_curves$T[i], 
                quality_curves$C[i], quality_curves$G[i])
    scores <- scores[!is.na(scores) & scores > 0]
    if (length(scores) > 0) quantile(scores, 0.10, na.rm = TRUE) else NA
  })
  
  quality_df$Q90 <- sapply(1:151, function(i) {
    scores <- c(quality_curves$A[i], quality_curves$T[i], 
                quality_curves$C[i], quality_curves$G[i])
    scores <- scores[!is.na(scores) & scores > 0]
    if (length(scores) > 0) quantile(scores, 0.90, na.rm = TRUE) else NA
  })
  
  # 绘制 (参考 fastqc_plot.R 样式：ribbons + mean line，Y轴根据实际数据自动调整)
  p <- ggplot(quality_df, aes(x = Cycle)) +
    geom_ribbon(aes(ymin = Q10, ymax = Q90), fill = "lightblue", alpha = 0.6) +
    geom_line(aes(y = Mean), color = "red", linewidth = 1.2) +
    # Y轴不设置limits，让ggplot根据实际数据自动调整范围
    scale_x_continuous(limits = c(1, 151), breaks = seq(0, 150, 25)) +
    labs(title = sprintf("Quality Distribution (R%d)", read_num),
         x = "Position in read (bp)",
         y = "Phred Quality Score") +
    theme_bw() +
    theme(plot.title = element_text(face = "bold", size = 16, hjust = 0.5),
          axis.title = element_text(size = 12),
          panel.grid.major = element_line(color = "gray90"),
          panel.grid.minor = element_blank()) +
    annotate("text", x = Inf, y = Inf, 
             label = "Red line: Mean quality\nBlue area: 10th-90th percentile",
             hjust = 1.1, vjust = 1.1, size = 3)
  
  save_plot_dual(
    plot_obj = p,
    filename_base = sprintf("0%d_quality_distribution_R%d", read_num + 2, read_num),
    width = 10,
    height = 6
  )
}

# 图5: 测序深度分布图
generate_depth_distribution <- function() {
  write_log("生成测序深度分布图...")
  
  # 读取depth文件
  depth_file <- file.path(ALIGN_DIR, sprintf("%s.depth", SAMPLE))
  depth_data <- read.table(depth_file, header = FALSE, sep = "\t",
                             col.names = c("chr", "pos", "depth"))
  
  # 限制深度范围0-500X
  depth_data$depth_capped <- pmin(depth_data$depth, 500)
  
  # 计算分布
  total_bases <- nrow(depth_data)
  depth_dist <- depth_data %>%
    group_by(depth = depth_capped) %>%
    summarise(count = n(), .groups = 'drop') %>%
    mutate(fraction = count / total_bases * 100)
  
  # 绘制 (使用平滑密度曲线，不填充)
  p <- ggplot(depth_data, aes(x = depth_capped)) +
    geom_density(color = TABLEAU_COLORS$blue, linewidth = 1.2, fill = NA) +
    scale_x_continuous(limits = c(0, 500), breaks = seq(0, 500, 100)) +
    labs(title = "Sequencing Depth Distribution",
         x = "Sequencing Depth (X)",
         y = "Density") +
    theme_bw() +
    theme(plot.title = element_text(face = "bold", size = 16, hjust = 0.5),
          axis.title = element_text(size = 12))
  
  save_plot_dual(
    plot_obj = p,
    filename_base = "05_depth_distribution",
    width = 10,
    height = 6
  )
}

# 图6: 插入片段长度分布图 (使用密度图，类似深度分布)
generate_insert_size_distribution <- function() {
  write_log("生成插入片段长度分布图...")
  
  # 从BAM文件提取的insert size数据
  insert_size_file <- file.path(OUTDIR, "insert_sizes.txt")
  
  # 读取数据
  insert_sizes <- read.table(insert_size_file, header = FALSE, col.names = "size")$size
  
  write_log(sprintf("  读取 %d 个insert size数据", length(insert_sizes)))
  
  # 创建数据框
  insert_df <- data.frame(Size = insert_sizes)
  
  # 绘制密度图 (类似深度分布图，使用Tableau蓝色，不填充)
  p <- ggplot(insert_df, aes(x = Size)) +
    geom_density(color = TABLEAU_COLORS$blue, linewidth = 1.2, fill = NA) +
    scale_x_continuous(limits = c(0, 500), breaks = seq(0, 500, 100)) +
    labs(title = "Insert Size Distribution",
         x = "Insert size (bp)",
         y = "# of reads") +
    theme_bw() +
    theme(plot.title = element_text(face = "bold", size = 16, hjust = 0.5),
          axis.title = element_text(size = 12))
  
  save_plot_dual(
    plot_obj = p,
    filename_base = "06_insert_size_distribution",
    width = 10,
    height = 6
  )
}

# 主函数
main <- function() {
  # 生成6张图
  generate_base_composition(1)      # 图1: 碱基组成 R1
  generate_base_composition(2)      # 图2: 碱基组成 R2
  generate_quality_distribution(1)  # 图3: 质量分布 R1
  generate_quality_distribution(2)  # 图4: 质量分布 R2
  generate_depth_distribution()     # 图5: 深度分布
  generate_insert_size_distribution() # 图6: 插入片段长度
  
  write_log("================================")
  write_log("所有QC图表生成完成")
  write_log("================================")
  write_log("生成文件:")
  for (i in 1:6) {
    files <- list.files(OUTDIR, pattern = sprintf("^0%d_", i), full.names = TRUE)
    for (f in files) {
      write_log(sprintf("  - %s", basename(f)))
    }
  }
  write_log("================================")
}

# 执行
tryCatch({
  main()
}, error = function(e) {
  write_log(sprintf("✗ 错误: %s", e$message))
  q(status = 1)
})
