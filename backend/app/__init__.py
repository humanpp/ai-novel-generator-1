from flask import Flask, jsonify, send_from_directory, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os

from .config import config
from .utils.logger import setup_logging


def create_app(config_name='development'):
    """Flask应用工厂函数"""
    # 计算前端目录路径
    current_dir = os.path.dirname(os.path.abspath(__file__))  # backend/app
    backend_dir = os.path.dirname(current_dir)  # backend
    project_dir = os.path.dirname(backend_dir)  # v5
    frontend_dir = os.path.join(project_dir, 'frontend')
    
    # 创建Flask应用，指定静态文件目录
    app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 配置日志
    setup_logging(app)
    
    # 初始化扩展
    CORS(app)
    
    # 导入并初始化数据库
    from .models.models import db
    db.init_app(app)
    
    # 注册蓝图
    from .routes import register_blueprints
    register_blueprints(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 注册前端路由
    @app.route('/')
    def serve_index():
        """提供前端首页"""
        return send_file(os.path.join(frontend_dir, 'index.html'))
    
    # 创建数据库表
    with app.app_context():
        # 确保目录存在
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)
        os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)
        
        # 创建所有表
        db.create_all()
        app.logger.info('数据库表初始化完成')
        
        # 初始化默认模型配置
        from .services.model_service import init_default_models
        init_default_models()
        app.logger.info('默认模型配置初始化完成')
    
    app.logger.info('应用初始化完成')
    return app


def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(400)
    def bad_request(error):
        app.logger.warning(f'[400] 请求参数错误: {error}')
        return jsonify({
            'success': False,
            'error': str(error.description) if hasattr(error, 'description') else '请求参数错误'
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        app.logger.warning(f'[404] 资源不存在: {error}')
        return jsonify({
            'success': False,
            'error': '请求的资源不存在'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        app.logger.warning(f'[405] 请求方法不允许: {error}')
        return jsonify({
            'success': False,
            'error': '不支持的请求方法'
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'[500] 服务器内部错误: {error}')
        return jsonify({
            'success': False,
            'error': '服务器内部错误'
        }), 500