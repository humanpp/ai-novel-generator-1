# v5/backend/app/utils/response.py
# 统一API响应格式工具

from flask import jsonify
import logging

# 获取日志记录器
logger = logging.getLogger(__name__)


def success(data=None, message='操作成功', code=200):
    """成功响应
    
    Args:
        data: 返回数据
        message: 提示消息
        code: HTTP状态码
    """
    response = {
        'success': True,
        'message': message
    }
    if data is not None:
        response['data'] = data
    
    return jsonify(response), code


def error(message='操作失败', code=400, details=None):
    """错误响应
    
    Args:
        message: 错误消息
        code: HTTP状态码
        details: 错误详情（可选）
    """
    response = {
        'success': False,
        'error': message
    }
    if details:
        response['details'] = details
    
    # 记录错误日志
    logger.error(f"[{code}] {message}")
    
    return jsonify(response), code


def created(data=None, message='创建成功'):
    """创建成功响应"""
    return success(data, message, 201)


def not_found(message='资源不存在'):
    """404响应"""
    return error(message, 404)


def bad_request(message='请求参数错误'):
    """400响应"""
    return error(message, 400)


def internal_error(message='服务器内部错误'):
    """500响应"""
    return error(message, 500)


def task_submitted(task_id, message='任务已提交'):
    """异步任务提交成功响应"""
    return success({
        'task_id': task_id
    }, message)
