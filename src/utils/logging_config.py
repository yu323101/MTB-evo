"""Logging configuration for MTB-Evo."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for terminal output."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        # 保存原始 levelname
        original_levelname = record.levelname
        
        # 添加颜色（仅在终端输出时）
        if sys.stdout.isatty():
            log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        
        result = super().format(record)
        
        # 恢复原始 levelname
        record.levelname = original_levelname
        return result


def setup_logging(
    log_file: Optional[Path] = None,
    verbose: bool = False,
    console_output: bool = True
) -> logging.Logger:
    """Setup logging configuration.
    
    Args:
        log_file: Path to log file (optional)
        verbose: If True, set DEBUG level; otherwise INFO
        console_output: If True, output to console
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("mtb_evo")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # 清除现有处理器
    logger.handlers = []
    
    # 格式定义
    console_format = ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setLevel(logging.DEBUG)  # 文件始终记录DEBUG级别
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get the mtb_evo logger or one of its child loggers."""
    base = logging.getLogger("mtb_evo")
    if not name:
        return base
    if name.startswith("mtb_evo"):
        return logging.getLogger(name)
    return base.getChild(name)
