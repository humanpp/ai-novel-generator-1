# v5/backend/app/routes/mindmap.py
# 章节-事件脑图API

from flask import Blueprint, request
from ..models.models import db, Novel
from ..services.character_service import build_chapter_event_mindmap, update_chapter_event_links
from ..utils.response import success, error, not_found, bad_request
from ..utils.logger import get_logger

logger = get_logger(__name__)

mindmap_bp = Blueprint('mindmap', __name__)


@mindmap_bp.route('/api/novels/<int:novel_id>/mindmap', methods=['GET'])
def get_chapter_event_mindmap(novel_id):
    """获取章节-事件脑图数据（节点+连线）"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        logger.info(f'获取章节-事件脑图: novel_id={novel_id}')
        data = build_chapter_event_mindmap(novel)
        return success(data)
    except Exception as e:
        logger.error(f'获取脑图失败: {e}', exc_info=True)
        return error(f'获取脑图失败: {str(e)}')


@mindmap_bp.route('/api/novels/<int:novel_id>/mindmap/links', methods=['PUT'])
def update_mindmap_links(novel_id):
    """批量更新章节-事件连线（覆盖式）
    
    请求体:
    {
        "links": [
            {"event_id": 1, "chapter_id": 2, "sort_order": 0},
            ...
        ]
    }
    """
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        data = request.get_json()
        if not data:
            return bad_request('请求体不能为空')
        
        links = data.get('links', [])
        if not isinstance(links, list):
            return bad_request('links 必须是数组')
        
        logger.info(f'更新脑图连线: novel_id={novel_id}, count={len(links)}')
        result = update_chapter_event_links(novel, links)
        return success(data=result, message=result['message'])
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新脑图连线失败: {e}', exc_info=True)
        return error(f'更新连线失败: {str(e)}')


@mindmap_bp.route('/api/novels/<int:novel_id>/mindmap/auto-map', methods=['POST'])
def auto_map_mindmap(novel_id):
    """自动映射事件到章节（然后返回更新后的脑图数据）"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        from ..services.chapter_service import auto_map_events_to_chapters
        map_result = auto_map_events_to_chapters(novel)
        
        logger.info(f'脑图自动映射完成: novel_id={novel_id}')
        data = build_chapter_event_mindmap(novel)
        data['mapping'] = map_result
        return success(data, message='自动映射完成')
    except Exception as e:
        db.session.rollback()
        logger.error(f'自动映射失败: {e}', exc_info=True)
        return error(f'自动映射失败: {str(e)}')
