# v5/backend/app/routes/models_config.py
# 模型配置API

from flask import Blueprint, request
from ..services.model_service import (
    get_all_models,
    get_model_by_id,
    get_default_model,
    create_model,
    update_model,
    delete_model,
    switch_default_model,
    test_model_connection
)
from ..utils.response import success, error, created, not_found, bad_request
from ..utils.logger import get_logger

logger = get_logger(__name__)

models_bp = Blueprint('models', __name__)


@models_bp.route('/api/models', methods=['GET'])
def list_models():
    """获取所有模型配置（API密钥脱敏）"""
    try:
        models = get_all_models()
        logger.info(f'获取模型列表: count={len(models)}')
        return success(models)
    except Exception as e:
        logger.error(f'获取模型列表失败: {e}')
        return error('获取模型列表失败')


@models_bp.route('/api/models/current-default', methods=['GET'])
def get_current_default():
    """获取当前默认模型"""
    try:
        model = get_default_model()
        if model:
            logger.info(f'获取默认模型: id={model.id}, name={model.name}')
            return success({
                'id': model.id,
                'name': model.name,
                'model_name': model.model_name
            })
        else:
            logger.info('未设置默认模型')
            return success(None, '未设置默认模型')
    except Exception as e:
        logger.error(f'获取默认模型失败: {e}')
        return error('获取默认模型失败')


@models_bp.route('/api/models', methods=['POST'])
def add_model():
    """添加新的模型配置"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['name', 'provider', 'base_url', 'model_name']
        for field in required_fields:
            if not data.get(field):
                return bad_request(f'缺少必填字段: {field}')
        
        model = create_model(data)
        logger.info(f'模型配置添加成功: id={model.id}, name={model.name}')
        return created(model.to_dict(), '模型配置添加成功')
    except Exception as e:
        logger.error(f'添加模型配置失败: {e}')
        return error('添加模型配置失败')


@models_bp.route('/api/models/test', methods=['POST'])
def test_model():
    """测试模型连接"""
    try:
        data = request.get_json()
        
        if not data.get('base_url') or not data.get('model_name'):
            return bad_request('缺少base_url或model_name')
        
        logger.info(f'测试模型连接: base_url={data.get("base_url")}, model={data.get("model_name")}')
        test_success, message = test_model_connection(data)
        
        if test_success:
            logger.info(f'模型连接测试成功: {message}')
        else:
            logger.warning(f'模型连接测试失败: {message}')
        
        return success({
            'success': test_success,
            'message': message
        })
    except Exception as e:
        logger.error(f'测试模型连接失败: {e}')
        return error('测试模型连接失败')


@models_bp.route('/api/models/<int:model_id>', methods=['PUT'])
def update_model_config(model_id):
    """更新模型配置"""
    try:
        data = request.get_json()
        model = update_model(model_id, data)
        logger.info(f'模型配置更新成功: id={model_id}')
        return success(model.to_dict(), '模型配置更新成功')
    except ValueError as e:
        logger.warning(f'更新模型配置失败: {e}')
        return not_found(str(e))
    except Exception as e:
        logger.error(f'更新模型配置失败: {e}')
        return error('更新模型配置失败')


@models_bp.route('/api/models/<int:model_id>', methods=['DELETE'])
def delete_model_config(model_id):
    """删除模型配置"""
    try:
        delete_model(model_id)
        logger.info(f'模型配置删除成功: id={model_id}')
        return success(message='模型配置删除成功')
    except ValueError as e:
        logger.warning(f'删除模型配置失败: {e}')
        return bad_request(str(e))
    except Exception as e:
        logger.error(f'删除模型配置失败: {e}')
        return error('删除模型配置失败')


@models_bp.route('/api/models/switch', methods=['POST'])
def switch_model():
    """切换默认模型"""
    try:
        data = request.get_json()
        model_id = data.get('model_id')
        
        if not model_id:
            return bad_request('缺少model_id')
        
        model = switch_default_model(model_id)
        logger.info(f'切换默认模型成功: id={model_id}, name={model.name}')
        return success(model.to_dict(), f'已切换默认模型为: {model.name}')
    except ValueError as e:
        logger.warning(f'切换默认模型失败: {e}')
        return not_found(str(e))
    except Exception as e:
        logger.error(f'切换默认模型失败: {e}')
        return error('切换默认模型失败')
