# v5/backend/app/services/model_service.py
# 模型配置服务

from flask import current_app
from ..models.models import db, ModelConfig
from ..utils.encryption import encrypt_api_key, decrypt_api_key


def init_default_models():
    """初始化默认模型配置"""
    try:
        # 检查是否已有内置模型
        builtin_count = ModelConfig.query.filter_by(is_builtin=True).count()
        if builtin_count > 0:
            return
        
        # 创建默认内置模型配置
        default_models = [
            {
                'name': 'OpenAI GPT-4',
                'provider': 'openai',
                'base_url': 'https://api.openai.com/v1',
                'api_key': '',  # 需要用户配置
                'model_name': 'gpt-4',
                'temperature': 0.7,
                'max_tokens': 4096,
                'is_default': False,
                'is_builtin': True
            },
            {
                'name': '本地模型 (Ollama)',
                'provider': 'custom',
                'base_url': 'http://localhost:11434/v1',
                'api_key': 'EMPTY',
                'model_name': 'llama2',
                'temperature': 0.7,
                'max_tokens': 2048,
                'is_default': False,
                'is_builtin': True
            }
        ]
        
        for model_data in default_models:
            model = ModelConfig(**model_data)
            db.session.add(model)
        
        db.session.commit()
        current_app.logger.info("默认模型配置初始化完成")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"初始化默认模型配置失败: {e}")


def get_all_models():
    """获取所有模型配置（API密钥脱敏）"""
    models = ModelConfig.query.order_by(ModelConfig.is_default.desc()).all()
    return [model.to_dict() for model in models]


def get_model_by_id(model_id):
    """根据ID获取模型配置"""
    return ModelConfig.query.get(model_id)


def get_default_model():
    """获取默认模型配置"""
    return ModelConfig.query.filter_by(is_default=True).first()


def create_model(data):
    """创建新的模型配置"""
    try:
        # 加密API密钥
        if data.get('api_key'):
            data['api_key'] = encrypt_api_key(data['api_key'])
        
        # 如果设置为默认，先取消其他默认
        if data.get('is_default'):
            ModelConfig.query.update({'is_default': False})
        
        model = ModelConfig(**data)
        db.session.add(model)
        db.session.commit()
        return model
    except Exception as e:
        db.session.rollback()
        raise


def update_model(model_id, data):
    """更新模型配置"""
    try:
        model = ModelConfig.query.get(model_id)
        if not model:
            raise ValueError("模型配置不存在")
        
        # 加密API密钥（如果提供）
        if 'api_key' in data and data['api_key'] and data['api_key'] != '****':
            data['api_key'] = encrypt_api_key(data['api_key'])
        elif data.get('api_key') == '****':
            # 保持原密钥不变
            del data['api_key']
        
        # 如果设置为默认，先取消其他默认
        if data.get('is_default'):
            ModelConfig.query.filter(ModelConfig.id != model_id).update({'is_default': False})
        
        # 更新字段
        for key, value in data.items():
            if hasattr(model, key):
                setattr(model, key, value)
        
        db.session.commit()
        return model
    except Exception as e:
        db.session.rollback()
        raise


def delete_model(model_id):
    """删除模型配置"""
    try:
        model = ModelConfig.query.get(model_id)
        if not model:
            raise ValueError("模型配置不存在")
        
        # 不允许删除内置模型
        if model.is_builtin:
            raise ValueError("不能删除内置模型")
        
        db.session.delete(model)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise


def switch_default_model(model_id):
    """切换默认模型"""
    try:
        model = ModelConfig.query.get(model_id)
        if not model:
            raise ValueError("模型配置不存在")
        
        # 取消所有默认
        ModelConfig.query.update({'is_default': False})
        
        # 设置新的默认
        model.is_default = True
        db.session.commit()
        return model
    except Exception as e:
        db.session.rollback()
        raise


def test_model_connection(config_data):
    """测试模型连接"""
    from ..llm.client import LLMClient
    
    try:
        # 如果API密钥是脱敏的，需要从数据库获取真实密钥
        if config_data.get('api_key') == '****':
            model_id = config_data.get('id')
            if model_id:
                model = ModelConfig.query.get(model_id)
                if model:
                    config_data['api_key'] = decrypt_api_key(model.api_key)
        
        client = LLMClient(config_data)
        return client.test_connection()
    except Exception as e:
        return False, f"测试失败: {str(e)}"