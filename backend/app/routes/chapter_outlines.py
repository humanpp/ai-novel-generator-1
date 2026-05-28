# v5/backend/app/routes/chapter_outlines.py
# 章节细纲API（流程A）

from flask import Blueprint, request
from ..models.models import db, Novel, Chapter, ChapterOutline
from ..services.chapter_service import generate_chapter_outlines, regenerate_single_outline, generate_single_chapter_outline
from ..utils.response import success, error, created, not_found, bad_request, task_submitted
from ..utils.logger import get_logger
from .tasks import create_task

logger = get_logger(__name__)

chapter_outlines_bp = Blueprint('chapter_outlines', __name__)


@chapter_outlines_bp.route('/api/novels/<int:novel_id>/chapter-outlines/generate', methods=['POST'])
def generate_chapter_outlines_api(novel_id):
    """批量生成章节细纲（需要先有章节）"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        data = request.get_json()
        
        logger.info(f'开始批量生成章节细纲: novel_id={novel_id}')
        
        # 定义异步任务函数
        def generate_task():
            novel_obj = db.session.get(Novel, novel_id)
            if not novel_obj:
                raise ValueError('项目不存在')
            return generate_chapter_outlines(novel_obj, data)
        
        task_id = create_task('generate_chapter_outlines', novel_id, generate_task)
        
        logger.info(f'批量生成章节细纲任务已提交: task_id={task_id}')
        return task_submitted(task_id, '章节细纲生成任务已提交')
    except Exception as e:
        logger.error(f'提交批量生成章节细纲任务失败: {e}')
        return error('提交批量生成章节细纲任务失败')


@chapter_outlines_bp.route('/api/novels/<int:novel_id>/chapter-outlines/<int:ch_no>/generate', methods=['POST'])
def generate_single_outline_api(novel_id, ch_no):
    """生成单章细纲（需要先有对应章节）"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        # 检查章节是否存在
        chapter = Chapter.query.filter_by(novel_id=novel_id, chapter_no=ch_no).first()
        if not chapter:
            return bad_request(f'章节{ch_no}不存在，请先创建章节')
        
        logger.info(f'开始生成单章细纲: novel_id={novel_id}, chapter_no={ch_no}')
        
        # 定义异步任务函数
        def generate_task():
            novel_obj = db.session.get(Novel, novel_id)
            if not novel_obj:
                raise ValueError('项目不存在')
            return generate_single_chapter_outline(novel_obj, ch_no)
        
        task_id = create_task('generate_single_outline', novel_id, generate_task)
        
        logger.info(f'单章细纲生成任务已提交: task_id={task_id}, chapter_no={ch_no}')
        return task_submitted(task_id, f'章节{ch_no}细纲生成任务已提交')
    except Exception as e:
        logger.error(f'提交单章细纲生成任务失败: {e}')
        return error('提交单章细纲生成任务失败')


@chapter_outlines_bp.route('/api/novels/<int:novel_id>/chapter-outlines', methods=['GET'])
def list_chapter_outlines(novel_id):
    """获取章节细纲列表"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        outlines = ChapterOutline.query.filter_by(novel_id=novel_id)\
            .order_by(ChapterOutline.chapter_no).all()
        
        logger.info(f'获取章节细纲列表: novel_id={novel_id}, count={len(outlines)}')
        return success([{
            'id': o.id,
            'chapter_no': o.chapter_no,
            'word_count': o.word_count,
            'content': o.content,
            'events': o.events
        } for o in outlines])
    except Exception as e:
        logger.error(f'获取章节细纲列表失败: {e}')
        return error('获取章节细纲列表失败')


@chapter_outlines_bp.route('/api/novels/<int:novel_id>/chapter-outlines/<int:ch_no>', methods=['GET'])
def get_chapter_outline(novel_id, ch_no):
    """获取单章细纲"""
    try:
        outline = ChapterOutline.query.filter_by(novel_id=novel_id, chapter_no=ch_no).first()
        if not outline:
            return not_found('章节细纲不存在')
        
        logger.info(f'获取单章细纲: novel_id={novel_id}, chapter_no={ch_no}')
        return success({
            'id': outline.id,
            'chapter_no': outline.chapter_no,
            'word_count': outline.word_count,
            'content': outline.content,
            'events': outline.events
        })
    except Exception as e:
        logger.error(f'获取单章细纲失败: {e}')
        return error('获取单章细纲失败')


@chapter_outlines_bp.route('/api/novels/<int:novel_id>/chapter-outlines/<int:ch_no>', methods=['PUT'])
def update_chapter_outline(novel_id, ch_no):
    """更新章节细纲"""
    try:
        outline = ChapterOutline.query.filter_by(novel_id=novel_id, chapter_no=ch_no).first()
        if not outline:
            return not_found('章节细纲不存在')
        
        data = request.get_json()
        
        if 'content' in data:
            if not isinstance(data['content'], str):
                return bad_request('内容必须是字符串')
            outline.content = data['content']
        
        if 'word_count' in data:
            if data['word_count'] is not None and not isinstance(data['word_count'], int):
                return bad_request('字数必须是整数')
            outline.word_count = data['word_count']
        
        db.session.commit()
        
        logger.info(f'章节细纲更新成功: novel_id={novel_id}, chapter_no={ch_no}')
        return success(message='章节细纲更新成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新章节细纲失败: {e}')
        return error('更新章节细纲失败')


@chapter_outlines_bp.route('/api/novels/<int:novel_id>/chapter-outlines/<int:ch_no>', methods=['DELETE'])
def delete_chapter_outline(novel_id, ch_no):
    """删除章节细纲"""
    try:
        outline = ChapterOutline.query.filter_by(novel_id=novel_id, chapter_no=ch_no).first()
        if not outline:
            return not_found('章节细纲不存在')
        
        db.session.delete(outline)
        db.session.commit()
        
        logger.info(f'章节细纲删除成功: novel_id={novel_id}, chapter_no={ch_no}')
        return success(message='章节细纲删除成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除章节细纲失败: {e}')
        return error('删除章节细纲失败')


@chapter_outlines_bp.route('/api/novels/<int:novel_id>/chapter-outlines/<int:ch_no>/regenerate', methods=['POST'])
def regenerate_chapter_outline(novel_id, ch_no):
    """重新生成章节细纲"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        # 检查章节是否存在
        chapter = Chapter.query.filter_by(novel_id=novel_id, chapter_no=ch_no).first()
        if not chapter:
            return bad_request(f'章节{ch_no}不存在，请先创建章节')
        
        logger.info(f'开始重新生成章节细纲: novel_id={novel_id}, chapter_no={ch_no}')
        
        # 定义异步任务函数
        def regenerate_task():
            novel_obj = db.session.get(Novel, novel_id)
            if not novel_obj:
                raise ValueError('项目不存在')
            return regenerate_single_outline(novel_obj, ch_no)
        
        task_id = create_task('regenerate_outline', novel_id, regenerate_task)
        
        logger.info(f'章节细纲重新生成任务已提交: task_id={task_id}, chapter_no={ch_no}')
        return task_submitted(task_id, '章节细纲重新生成任务已提交')
    except Exception as e:
        logger.error(f'提交章节细纲重新生成任务失败: {e}')
        return error('提交章节细纲重新生成任务失败')
