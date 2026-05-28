# v5/backend/app/utils/logger.py
# 日志配置

import logging
import os
from datetime import datetime


def setup_logging(app):
    """配置日志系统
    
    Args:
        app: Flask应用实例
    """
    # 创建日志目录
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 日志文件路径
    log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')
    
    # 配置日志格式
    log_format = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 配置应用日志
    app.logger.setLevel(logging.DEBUG)
    
    # 记录启动日志
    app.logger.info('=' * 50)
    app.logger.info('AI小说工坊后端服务启动')
    app.logger.info(f'日志文件: {log_file}')
    app.logger.info('=' * 50)


def get_logger(name):
    """获取日志记录器
    
    Args:
        name: 日志记录器名称（通常使用模块名）
    """
    return logging.getLogger(name)
