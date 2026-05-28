# v5/backend/app/routes/chapters.py
# 章节正文API

from flask import Blueprint, request
from ..models.models import db, Novel, Chapter, ChapterVersion, ChapterCharacter, ChapterEventMapping
from ..services.chapter_service import generate_chapter_content, batch_generate_chapters, auto_map_events_to_chapters
from ..utils.response import success, error, created, not_found, bad_request, task_submitted
from ..utils.logger import get_logger
from .tasks import create_task

logger = get_logger(__name__)

chapters_bp = Blueprint('chapters', __name__)


@chapters_bp.route('/api/novels/<int:novel_id>/chapters', methods=['POST'])
def create_chapter(novel_id):
    """创建新章节"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        data = request.get_json()
        chapter_no = data.get('chapter_no')
        title = data.get('title', f'第{chapter_no}章')
        
        # 检查章节是否已存在
        existing = Chapter.query.filter_by(novel_id=novel_id, chapter_no=chapter_no).first()
        if existing:
            return bad_request('章节已存在')
        
        # 创建新章节
        chapter = Chapter(
            novel_id=novel_id,
            chapter_no=chapter_no,
            title=title,
            content='',
            word_count=0
        )
        db.session.add(chapter)
        db.session.commit()
        
        logger.info(f'章节创建成功: novel_id={novel_id}, chapter_no={chapter_no}, title={title}')
        return created({
            'id': chapter.id,
            'chapter_no': chapter.chapter_no,
            'title': chapter.title
        }, '章节创建成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f'创建章节失败: {e}')
        return error('创建章节失败')


@chapters_bp.route('/api/novels/<int:novel_id>/chapters/<int:ch_no>/generate', methods=['POST'])
def generate_chapter(novel_id, ch_no):
    """生成单章正文（异步任务）"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        logger.info(f'开始生成章节正文: novel_id={novel_id}, chapter_no={ch_no}')
        
        # 定义异步任务函数
        def generate_task():
            # 在任务内部重新查询，避免Session绑定问题
            novel_obj = db.session.get(Novel, novel_id)
            if not novel_obj:
                raise ValueError('项目不存在')
            return generate_chapter_content(novel_obj, ch_no)
        
        # 使用异步任务方式
        task_id = create_task('generate_chapter', novel_id, generate_task)
        
        logger.info(f'章节生成任务已提交: task_id={task_id}')
        return task_submitted(task_id, '章节生成任务已提交')
    except Exception as e:
        logger.error(f'提交章节生成任务失败: {e}')
        return error('提交章节生成任务失败')


@chapters_bp.route('/api/novels/<int:novel_id>/chapters/generate-batch', methods=['POST'])
def generate_chapters_batch(novel_id):
    """批量生成章节"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        data = request.get_json()
        chapter_numbers = data.get('chapter_numbers', [])
        
        if not chapter_numbers:
            return bad_request('章节列表不能为空')
        
        logger.info(f'开始批量生成章节: novel_id={novel_id}, chapters={chapter_numbers}')
        
        result = batch_generate_chapters(novel, chapter_numbers)
        
        return task_submitted(result.get('task_id'), '批量生成任务已提交')
    except Exception as e:
        logger.error(f'提交批量生成任务失败: {e}')
        return error('提交批量生成任务失败')


@chapters_bp.route('/api/novels/<int:novel_id>/chapters', methods=['GET'])
def list_chapters(novel_id):
    """获取章节列表"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        chapters = Chapter.query.filter_by(novel_id=novel_id)\
            .order_by(Chapter.chapter_no).all()
        
        logger.info(f'获取章节列表: novel_id={novel_id}, count={len(chapters)}')
        return success([{
            'id': c.id,
            'chapter_no': c.chapter_no,
            'title': c.title,
            'word_count': c.word_count,
            'generated_at': c.generated_at.isoformat() if c.generated_at else None,
            'has_content': bool(c.content)
        } for c in chapters])
    except Exception as e:
        logger.error(f'获取章节列表失败: {e}')
        return error('获取章节列表失败')


@chapters_bp.route('/api/novels/<int:novel_id>/chapters/<int:ch_no>', methods=['GET'])
def get_chapter(novel_id, ch_no):
    """获取章节内容"""
    try:
        chapter = Chapter.query.filter_by(novel_id=novel_id, chapter_no=ch_no).first()
        if not chapter:
            return not_found('章节不存在')
        
        # 获取版本信息
        versions = ChapterVersion.query.filter_by(chapter_id=chapter.id)\
            .order_by(ChapterVersion.version.desc()).all()
        
        logger.info(f'获取章节内容: novel_id={novel_id}, chapter_no={ch_no}')
        return success({
            'id': chapter.id,
            'chapter_no': chapter.chapter_no,
            'title': chapter.title,
            'content': chapter.content,
            'word_count': chapter.word_count,
            'generated_at': chapter.generated_at.isoformat() if chapter.generated_at else None,
            'current_version': len(versions),
            'versions': [{
                'id': v.id,
                'version': v.version,
                'word_count': v.word_count,
                'created_at': v.created_at.isoformat() if v.created_at else None
            } for v in versions]
        })
    except Exception as e:
        logger.error(f'获取章节内容失败: {e}')
        return error('获取章节内容失败')


@chapters_bp.route('/api/novels/<int:novel_id>/chapters/<int:ch_no>', methods=['PUT'])
def update_chapter(novel_id, ch_no):
    """更新章节内容"""
    try:
        chapter = Chapter.query.filter_by(novel_id=novel_id, chapter_no=ch_no).first()
        if not chapter:
            return not_found('章节不存在')
        
        data = request.get_json()
        
        # 保存当前版本
        if chapter.content:
            current_version = ChapterVersion.query.filter_by(chapter_id=chapter.id)\
                .order_by(ChapterVersion.version.desc()).first()
            new_version_num = (current_version.version + 1) if current_version else 1
            
            version = ChapterVersion(
                chapter_id=chapter.id,
                version=new_version_num,
                content=chapter.content,
                word_count=chapter.word_count
            )
            db.session.add(version)
        
        # 更新内容
        if 'content' in data:
            chapter.content = data['content']
            chapter.word_count = len(data['content'])
        if 'title' in data:
            chapter.title = data['title']
        
        db.session.commit()
        
        logger.info(f'章节更新成功: novel_id={novel_id}, chapter_no={ch_no}')
        return success(message='章节更新成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新章节失败: {e}')
        return error('更新章节失败')


@chapters_bp.route('/api/novels/<int:novel_id>/chapters/<int:ch_no>', methods=['DELETE'])
def delete_chapter(novel_id, ch_no):
    """删除章节"""
    try:
        chapter = Chapter.query.filter_by(novel_id=novel_id, chapter_no=ch_no).first()
        if not chapter:
            return not_found('章节不存在')
        
        db.session.delete(chapter)
        db.session.commit()
        
        logger.info(f'章节删除成功: novel_id={novel_id}, chapter_no={ch_no}')
        return success(message='章节删除成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除章节失败: {e}')
        return error('删除章节失败')


@chapters_bp.route('/api/novels/<int:novel_id>/chapters/<int:ch_no>/regenerate', methods=['POST'])
def regenerate_chapter(novel_id, ch_no):
    """重新生成章节"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        logger.info(f'开始重新生成章节: novel_id={novel_id}, chapter_no={ch_no}')
        
        # 定义异步任务函数
        def regenerate_task():
            novel_obj = db.session.get(Novel, novel_id)
            if not novel_obj:
                raise ValueError('项目不存在')
            return generate_chapter_content(novel_obj, ch_no)
        
        task_id = create_task('regenerate_chapter', novel_id, regenerate_task)
        
        logger.info(f'章节重新生成任务已提交: task_id={task_id}')
        return task_submitted(task_id, '章节重新生成任务已提交')
    except Exception as e:
        logger.error(f'提交章节重新生成任务失败: {e}')
        return error('提交章节重新生成任务失败')


@chapters_bp.route('/api/novels/<int:novel_id>/chapters/<int:ch_no>/versions', methods=['GET'])
def list_chapter_versions(novel_id, ch_no):
    """获取章节版本列表"""
    try:
        chapter = Chapter.query.filter_by(novel_id=novel_id, chapter_no=ch_no).first()
        if not chapter:
            return not_found('章节不存在')
        
        versions = ChapterVersion.query.filter_by(chapter_id=chapter.id)\
            .order_by(ChapterVersion.version.desc()).all()
        
        logger.info(f'获取章节版本列表: novel_id={novel_id}, chapter_no={ch_no}, count={len(versions)}')
        return success([{
            'id': v.id,
            'version': v.version,
            'word_count': v.word_count,
            'created_at': v.created_at.isoformat() if v.created_at else None
        } for v in versions])
    except Exception as e:
        logger.error(f'获取章节版本列表失败: {e}')
        return error('获取章节版本列表失败')


@chapters_bp.route('/api/novels/<int:novel_id>/chapters/<int:ch_no>/rollback', methods=['POST'])
def rollback_chapter(novel_id, ch_no):
    """回滚章节版本"""
    try:
        chapter = Chapter.query.filter_by(novel_id=novel_id, chapter_no=ch_no).first()
        if not chapter:
            return not_found('章节不存在')
        
        data = request.get_json()
        version = data.get('version')
        
        # 查找指定版本
        version_record = ChapterVersion.query.filter_by(
            chapter_id=chapter.id,
            version=version
        ).first()
        
        if not version_record:
            return not_found('版本不存在')
        
        # 保存当前版本
        current_version = ChapterVersion.query.filter_by(chapter_id=chapter.id)\
            .order_by(ChapterVersion.version.desc()).first()
        new_version_num = (current_version.version + 1) if current_version else 1
        
        new_version = ChapterVersion(
            chapter_id=chapter.id,
            version=new_version_num,
            content=chapter.content,
            word_count=chapter.word_count
        )
        db.session.add(new_version)
        
        # 回滚到指定版本
        chapter.content = version_record.content
        chapter.word_count = version_record.word_count
        
        db.session.commit()
        
        logger.info(f'章节回滚成功: novel_id={novel_id}, chapter_no={ch_no}, version={version}')
        return success(message='章节回滚成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f'章节回滚失败: {e}')
        return error('章节回滚失败')


# ===== 章节事件映射接口（流程B专用）=====

@chapters_bp.route('/api/novels/<int:novel_id>/chapters/<int:ch_no>/events', methods=['GET'])
def get_chapter_events(novel_id, ch_no):
    """获取该章节关联的事件列表及排序"""
    try:
        chapter = Chapter.query.filter_by(novel_id=novel_id, chapter_no=ch_no).first()
        if not chapter:
            return not_found('章节不存在')
        
        mappings = ChapterEventMapping.query.filter_by(chapter_id=chapter.id)\
            .order_by(ChapterEventMapping.sort_order).all()
        
        events = []
        for mapping in mappings:
            event = EventOutline.query.get(mapping.event_id)
            if event:
                events.append({
                    'mapping_id': mapping.id,
                    'event_id': event.id,
                    'event_no': event.event_no,
                    'title': event.title,
                    'description': event.description,
                    'cause': event.cause,
                    'effect': event.effect,
                    'related_characters': event.related_characters,
                    'sort_order': mapping.sort_order
                })
        
        # 同时获取所有可用事件（未分配给任何章节的）
        all_events = EventOutline.query.filter_by(novel_id=novel_id)\
            .order_by(EventOutline.event_no).all()
        assigned_event_ids = {e['event_id'] for e in events}
        unassigned = [{
            'event_id': e.id,
            'event_no': e.event_no,
            'title': e.title,
            'description': e.description,
            'cause': e.cause,
            'effect': e.effect,
        } for e in all_events if e.id not in assigned_event_ids]
        
        logger.info(f'获取章节事件: novel_id={novel_id}, ch_no={ch_no}, assigned={len(events)}, unassigned={len(unassigned)}')
        return success({
            'chapter_title': chapter.title,
            'assigned_events': events,
            'unassigned_events': unassigned,
            'total_events': len(all_events)
        })
    except Exception as e:
        logger.error(f'获取章节事件失败: {e}')
        return error('获取章节事件失败')


@chapters_bp.route('/api/novels/<int:novel_id>/chapters/<int:ch_no>/events', methods=['PUT'])
def update_chapter_events(novel_id, ch_no):
    """手动调整该章关联的事件及排序"""
    try:
        chapter = Chapter.query.filter_by(novel_id=novel_id, chapter_no=ch_no).first()
        if not chapter:
            return not_found('章节不存在')
        
        data = request.get_json()
        event_ids = data.get('event_ids', [])  # 按顺序排列的事件ID列表
        
        # 清除现有映射
        ChapterEventMapping.query.filter_by(chapter_id=chapter.id).delete()
        
        # 建立新映射
        for sort_order, event_id in enumerate(event_ids):
            mapping = ChapterEventMapping(
                chapter_id=chapter.id,
                event_id=event_id,
                sort_order=sort_order
            )
            db.session.add(mapping)
        
        db.session.commit()
        
        logger.info(f'章节事件更新成功: novel_id={novel_id}, ch_no={ch_no}, count={len(event_ids)}')
        return success(message=f'已更新 {len(event_ids)} 个事件', data={'assigned_count': len(event_ids)})
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新章节事件失败: {e}')
        return error('更新章节事件失败')


@chapters_bp.route('/api/novels/<int:novel_id>/chapters/<int:ch_no>/events/auto-map', methods=['POST'])
def auto_map_chapter_events(novel_id, ch_no):
    """对该章重新执行事件映射"""
    try:
        chapter = Chapter.query.filter_by(novel_id=novel_id, chapter_no=ch_no).first()
        if not chapter:
            return not_found('章节不存在')
        
        from ..services.chapter_service import auto_map_events_for_chapter
        result = auto_map_events_for_chapter(novel_id, chapter)
        
        logger.info(f'章节事件自动映射完成: novel_id={novel_id}, ch_no={ch_no}')
        return success(data=result, message='事件自动映射完成')
    except Exception as e:
        logger.error(f'自动映射失败: {e}')
        return error('自动映射事件失败')


@chapters_bp.route('/api/novels/<int:novel_id>/events/auto-map', methods=['POST'])
def auto_map_all_events(novel_id):
    """全局自动映射所有事件到章节"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        from ..services.chapter_service import auto_map_events_to_chapters
        result = auto_map_events_to_chapters(novel)
        
        logger.info(f'全局事件自动映射完成: novel_id={novel_id}')
        return success(data=result, message='全局事件自动映射完成')
    except Exception as e:
        logger.error(f'全局自动映射失败: {e}')
        return error('全局自动映射事件失败')
