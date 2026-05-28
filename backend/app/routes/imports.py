# v5/backend/app/routes/imports.py
# 导入与反推API

from flask import Blueprint, request
from ..models.models import db, Novel, Chapter, ChapterOutline, Character, ImportRecord
from ..services.import_service import upload_and_parse, reverse_outline_from_outlines, reverse_chapter_outline, reverse_characters_from_chapter
from ..utils.response import success, error, created, not_found, bad_request
from ..utils.logger import get_logger
import os

logger = get_logger(__name__)

imports_bp = Blueprint('imports', __name__)


@imports_bp.route('/api/novels/import', methods=['POST'])
def import_novel():
    """上传小说文件"""
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return bad_request('没有上传文件')
        
        file = request.files['file']
        if file.filename == '':
            return bad_request('文件名为空')
        
        # 获取参数
        novel_id = request.form.get('novel_id')
        
        # 如果没有指定项目，创建新项目
        if not novel_id:
            novel = Novel(
                title=os.path.splitext(file.filename)[0],
                format='long',
                workflow_mode='chapter',
                summary=f'从文件 {file.filename} 导入'
            )
            db.session.add(novel)
            db.session.flush()
            novel_id = novel.id
            logger.info(f'创建新项目: id={novel_id}, title={novel.title}')
        
        # 上传并解析文件
        logger.info(f'开始导入文件: novel_id={novel_id}, file={file.filename}')
        import_record = upload_and_parse(file, novel_id)
        
        logger.info(f'文件导入成功: import_id={import_record.id}, novel_id={novel_id}')
        return created({
            'import_id': import_record.id,
            'novel_id': novel_id,
            'file_name': import_record.file_name,
            'status': import_record.status
        }, '文件上传成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f'导入文件失败: {e}')
        return error('导入文件失败')


@imports_bp.route('/api/novels/<int:novel_id>/reverse-outline', methods=['POST'])
def reverse_outline_api(novel_id):
    """反推大纲（长篇：从所有章节细纲反推；短篇：从正文反推）"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        logger.info(f'开始反推大纲: novel_id={novel_id}, format={novel.format}')
        result = reverse_outline_from_outlines(novel)
        
        logger.info(f'大纲反推成功: novel_id={novel_id}')
        return success(result, '大纲反推成功')
    except ValueError as e:
        logger.warning(f'反推大纲条件不满足: {e}')
        return error(str(e))
    except Exception as e:
        logger.error(f'反推大纲失败: {e}')
        return error('反推大纲失败')


@imports_bp.route('/api/novels/<int:novel_id>/chapters/<int:ch_no>/reverse-outline', methods=['POST'])
def reverse_chapter_outline_api(novel_id, ch_no):
    """反推单章细纲"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        # 检查章节是否存在
        chapter = Chapter.query.filter_by(novel_id=novel_id, chapter_no=ch_no).first()
        if not chapter:
            return not_found(f'章节{ch_no}不存在')
        
        logger.info(f'开始反推章节细纲: novel_id={novel_id}, chapter_no={ch_no}')
        result = reverse_chapter_outline(novel, chapter)
        
        logger.info(f'章节细纲反推成功: novel_id={novel_id}, chapter_no={ch_no}')
        return success(result, f'章节{ch_no}细纲反推成功')
    except Exception as e:
        logger.error(f'反推章节细纲失败: {e}')
        return error('反推章节细纲失败')


@imports_bp.route('/api/novels/<int:novel_id>/chapters/<int:ch_no>/reverse-characters', methods=['POST'])
def reverse_characters_from_chapter_api(novel_id, ch_no):
    """从单章反推角色"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        # 检查章节是否存在
        chapter = Chapter.query.filter_by(novel_id=novel_id, chapter_no=ch_no).first()
        if not chapter:
            return not_found(f'章节{ch_no}不存在')
        
        logger.info(f'开始从章节反推角色: novel_id={novel_id}, chapter_no={ch_no}')
        result = reverse_characters_from_chapter(novel, chapter)
        
        logger.info(f'角色反推成功: novel_id={novel_id}, chapter_no={ch_no}, created={result.get("created_count", 0)}')
        return success(result, '角色反推成功')
    except Exception as e:
        logger.error(f'反推角色失败: {e}')
        return error('反推角色失败')


@imports_bp.route('/api/import-records', methods=['GET'])
def list_import_records():
    """获取导入记录列表"""
    try:
        records = ImportRecord.query.order_by(ImportRecord.import_time.desc()).all()
        
        logger.info(f'获取导入记录列表: count={len(records)}')
        return success([{
            'id': r.id,
            'novel_id': r.novel_id,
            'file_name': r.file_name,
            'import_time': r.import_time.isoformat() if r.import_time else None,
            'status': r.status
        } for r in records])
    except Exception as e:
        logger.error(f'获取导入记录列表失败: {e}')
        return error('获取导入记录列表失败')


@imports_bp.route('/api/import-records/<int:record_id>', methods=['GET'])
def get_import_record(record_id):
    """获取单条导入记录详情"""
    try:
        record = ImportRecord.query.get(record_id)
        if not record:
            return not_found('记录不存在')
        
        logger.info(f'获取导入记录详情: record_id={record_id}')
        return success({
            'id': record.id,
            'novel_id': record.novel_id,
            'file_name': record.file_name,
            'file_path': record.file_path,
            'import_time': record.import_time.isoformat() if record.import_time else None,
            'status': record.status
        })
    except Exception as e:
        logger.error(f'获取导入记录详情失败: {e}')
        return error('获取导入记录详情失败')
