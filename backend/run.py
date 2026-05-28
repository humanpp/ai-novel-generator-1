#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI网文小说生成软件 - 后端启动脚本
"""

import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# 创建应用实例
app = create_app('development')

if __name__ == '__main__':
    print("=" * 50)
    print("AI网文小说生成软件 - 后端服务")
    print("=" * 50)
    print(f"服务地址: http://localhost:5000")
    print(f"调试模式: {app.config['DEBUG']}")
    print(f"数据库: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )