# v5/backend/app/routes/novels.py
# 项目管理API

from flask import Blueprint, request
from ..models.models import db, Novel, Outline, WritingStats
from ..utils.response import success, error, created, not_found, bad_request
from ..utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

novels_bp = Blueprint('novels', __name__)


@novels_bp.route('/api/novels', methods=['GET'])
def list_novels():
    """获取项目列表"""
    try:
        novels = Novel.query.order_by(Novel.updated_at.desc()).all()
        logger.info(f'获取项目列表成功，共 {len(novels)} 个项目')
        return success([novel_to_dict(novel) for novel in novels])
    except Exception as e:
        logger.error(f'获取项目列表失败: {e}')
        return error('获取项目列表失败')


@novels_bp.route('/api/novels', methods=['POST'])
def create_novel():
    """创建新项目"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        if not data.get('title'):
            return bad_request('标题不能为空')
        
        if not data.get('workflow_mode') or data['workflow_mode'] not in ['chapter', 'event']:
            return bad_request('工作流模式必须是chapter或event')
        
        if data.get('format') and data['format'] not in ['long', 'short']:
            return bad_request('格式必须是long或short')
        
        # 创建项目
        novel = Novel(
            title=data['title'],
            genre=data.get('genre', ''),
            format=data.get('format', 'long'),
            workflow_mode=data['workflow_mode'],
            summary=data.get('summary', '')
        )
        db.session.add(novel)
        db.session.flush()  # 获取ID
        
        # 创建关联的大纲
        outline = Outline(novel_id=novel.id, content='', version=1)
        db.session.add(outline)
        
        # 创建关联的写作统计
        stats = WritingStats(novel_id=novel.id)
        db.session.add(stats)
        
        db.session.commit()
        
        logger.info(f'项目创建成功: id={novel.id}, title={novel.title}')
        return created(novel_to_dict(novel), '项目创建成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f'创建项目失败: {e}')
        return error('创建项目失败')


@novels_bp.route('/api/novels/<int:novel_id>', methods=['GET'])
def get_novel(novel_id):
    """获取项目详情"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        result = novel_to_dict(novel)
        # 包含大纲信息
        if novel.outline:
            result['outline'] = {
                'id': novel.outline.id,
                'version': novel.outline.version,
                'has_content': bool(novel.outline.content)
            }
        
        logger.info(f'获取项目详情: id={novel_id}')
        return success(result)
    except Exception as e:
        logger.error(f'获取项目详情失败: {e}')
        return error('获取项目详情失败')


@novels_bp.route('/api/novels/<int:novel_id>', methods=['PUT'])
def update_novel(novel_id):
    """更新项目"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        data = request.get_json()
        
        # 更新允许的字段
        if 'title' in data:
            novel.title = data['title']
        if 'genre' in data:
            novel.genre = data['genre']
        if 'summary' in data:
            novel.summary = data['summary']
        
        novel.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f'项目更新成功: id={novel_id}')
        return success(novel_to_dict(novel), '项目更新成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新项目失败: {e}')
        return error('更新项目失败')


@novels_bp.route('/api/novels/<int:novel_id>', methods=['DELETE'])
def delete_novel(novel_id):
    """删除项目"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        title = novel.title
        db.session.delete(novel)
        db.session.commit()
        
        logger.info(f'项目删除成功: id={novel_id}, title={title}')
        return success(message='项目删除成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除项目失败: {e}')
        return error('删除项目失败')


def novel_to_dict(novel):
    """将Novel对象转换为字典"""
    return {
        'id': novel.id,
        'title': novel.title,
        'genre': novel.genre,
        'format': novel.format,
        'workflow_mode': novel.workflow_mode,
        'summary': novel.summary,
        'created_at': novel.created_at.isoformat() if novel.created_at else None,
        'updated_at': novel.updated_at.isoformat() if novel.updated_at else None
    }
