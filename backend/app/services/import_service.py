# v5/backend/app/services/import_service.py
# 导入服务

from flask import current_app
from ..models.models import db, Novel, Chapter, ChapterOutline, Character, ImportRecord
from ..utils.file_utils import parse_txt, parse_docx
from ..utils.json_parser import parse_llm_json_response
import os
import uuid
import re


from ..prompts import (
    get_reverse_chapter_outline_prompt,
    get_reverse_outline_short_prompt,
    get_reverse_outline_long_prompt,
    get_reverse_characters_prompt,
)

def split_content_to_chapters(content, novel_format='long'):
    """
    将内容分割成章节
    
    Args:
        content: 小说内容
        novel_format: 'long' 或 'short'
    
    Returns:
        章节列表 [{'chapter_no': 1, 'title': '标题', 'content': '内容'}, ...]
    """
    if novel_format == 'short':
        # 短篇直接作为一章
        return [{
            'chapter_no': 1,
            'title': '全文',
            'content': content
        }]
    
    # 长篇按章节分割
    # 常见的章节格式：
    # 第1章、第一章、Chapter 1、第 1 章、【第1章】等
    chapter_patterns = [
        r'^第[一二三四五六七八九十百千万\d]+章\s*.*$',  # 第X章
        r'^第\s*\d+\s*章\s*.*$',  # 第 X 章
        r'^Chapter\s*\d+\s*.*$',  # Chapter X
        r'^CHAPTER\s*\d+\s*.*$',  # CHAPTER X
        r'^\d+\.\s+.*$',  # 1. 标题
        r'^【第[一二三四五六七八九十百千万\d]+章】.*$',  # 【第X章】
    ]
    
    # 合并所有模式
    combined_pattern = '|'.join(f'({p})' for p in chapter_patterns)
    
    # 按行分割
    lines = content.split('\n')
    
    chapters = []
    current_chapter = None
    current_content = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # 检查是否是章节标题
        if line_stripped and re.match(combined_pattern, line_stripped, re.MULTILINE | re.IGNORECASE):
            # 保存之前的章节
            if current_chapter is not None:
                current_chapter['content'] = '\n'.join(current_content).strip()
                if current_chapter['content']:
                    chapters.append(current_chapter)
            
            # 开始新章节
            current_chapter = {
                'chapter_no': len(chapters) + 1,
                'title': line_stripped,
                'content': ''
            }
            current_content = []
        else:
            current_content.append(line)
    
    # 保存最后一个章节
    if current_chapter is not None:
        current_chapter['content'] = '\n'.join(current_content).strip()
        if current_chapter['content']:
            chapters.append(current_chapter)
    
    # 如果没有找到章节分割，按段落数平均分割
    if not chapters:
        # 尝试按空行分割段落
        paragraphs = re.split(r'\n\s*\n', content)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        if len(paragraphs) > 10:
            # 按每10个段落一章分割
            chunk_size = 10
            for i in range(0, len(paragraphs), chunk_size):
                chunk = paragraphs[i:i+chunk_size]
                chapters.append({
                    'chapter_no': len(chapters) + 1,
                    'title': f'第{len(chapters) + 1}章',
                    'content': '\n\n'.join(chunk)
                })
        else:
            # 内容不多，作为一章
            chapters.append({
                'chapter_no': 1,
                'title': '第1章',
                'content': content
            })
    
    return chapters


def upload_and_parse(file_storage, novel_id):
    """上传并解析文件，自动创建章节"""
    try:
        # 生成唯一文件名
        file_ext = os.path.splitext(file_storage.filename)[1]
        unique_name = f"{uuid.uuid4()}{file_ext}"
        
        # 保存文件
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, unique_name)
        file_storage.save(file_path)
        
        # 创建导入记录
        import_record = ImportRecord(
            novel_id=novel_id,
            file_name=file_storage.filename,
            file_path=file_path,
            status='processing'
        )
        db.session.add(import_record)
        db.session.flush()
        
        # 获取项目信息
        novel = Novel.query.get(novel_id)
        if not novel:
            raise ValueError('项目不存在')
        
        # 解析文件内容
        if file_path.endswith('.txt'):
            content = parse_txt(file_path)
        elif file_path.endswith('.docx'):
            content = parse_docx(file_path)
        else:
            raise ValueError(f'不支持的文件格式: {file_ext}')
        
        # 分割章节
        chapters_data = split_content_to_chapters(content, novel.format)
        
        # 创建章节
        for ch_data in chapters_data:
            chapter = Chapter(
                novel_id=novel_id,
                chapter_no=ch_data['chapter_no'],
                title=ch_data['title'],
                content=ch_data['content'],
                word_count=len(ch_data['content'])
            )
            db.session.add(chapter)
        
        # 更新导入状态
        import_record.status = 'done'
        db.session.commit()
        
        current_app.logger.info(f'导入成功: {len(chapters_data)} 个章节已创建')
        
        return import_record
    except Exception as e:
        db.session.rollback()
        raise


def get_llm_client():
    """获取LLM客户端"""
    from ..llm.client import LLMClient
    from ..utils.encryption import decrypt_api_key
    from .model_service import get_default_model
    
    model = get_default_model()
    if not model:
        raise ValueError("未配置默认模型")
    
    api_key = decrypt_api_key(model.api_key) if model.api_key else ''
    config = {
        'base_url': model.base_url,
        'api_key': api_key,
        'model_name': model.model_name,
        'temperature': model.temperature,
        'max_tokens': model.max_tokens
    }
    return LLMClient(config)


def reverse_chapter_outline(novel, chapter):
    """从单章内容反推细纲"""
    try:
        client = get_llm_client()
        
        # 截取内容（避免太长）
        content = chapter.content[:3000] if len(chapter.content) > 3000 else chapter.content
        
        prompt = get_reverse_chapter_outline_prompt(novel.title, novel.genre, chapter.title, content, novel.summary or '')
        
        response = client.complete(prompt)
        
        # 保存或更新章节细纲
        outline = ChapterOutline.query.filter_by(
            novel_id=novel.id,
            chapter_no=chapter.chapter_no
        ).first()
        
        if outline:
            outline.content = response
            outline.word_count = len(response)
        else:
            outline = ChapterOutline(
                novel_id=novel.id,
                chapter_no=chapter.chapter_no,
                content=response,
                word_count=len(response)
            )
            db.session.add(outline)
        
        db.session.commit()
        
        return {
            'chapter_no': chapter.chapter_no,
            'content': response,
            'message': '章节细纲反推成功'
        }
    except Exception as e:
        db.session.rollback()
        raise


def reverse_outline_from_outlines(novel):
    """从所有章节细纲反推大纲（长篇）或从正文反推大纲（短篇）"""
    try:
        client = get_llm_client()
        
        if novel.format == 'short':
            # 短篇：从正文反推大纲
            chapters = Chapter.query.filter_by(novel_id=novel.id).all()
            content = '\n\n'.join([c.content for c in chapters if c.content])
            content = content[:5000] if len(content) > 5000 else content
            
            prompt = get_reverse_outline_short_prompt(novel.title, novel.genre, content, novel.summary or '')
        else:
            # 长篇：从所有章节细纲反推大纲
            outlines = ChapterOutline.query.filter_by(novel_id=novel.id)\
                .order_by(ChapterOutline.chapter_no).all()
            
            if not outlines:
                raise ValueError('请先为各章节生成细纲，再反推大纲')
            
            outlines_text = '\n\n'.join([
                f"第{o.chapter_no}章细纲：\n{o.content}"
                for o in outlines if o.content
            ])
            
            prompt = get_reverse_outline_long_prompt(novel.title, novel.genre, outlines_text, novel.summary or '')
        
        outline_content = client.complete(prompt)
        
        # 保存大纲
        from ..services.outline_service import update_outline_content
        update_outline_content(novel, outline_content)
        
        return {
            'outline': outline_content,
            'message': '大纲反推成功'
        }
    except Exception as e:
        raise


def reverse_characters_from_chapter(novel, chapter):
    """从单章内容反推角色"""
    try:
        client = get_llm_client()
        
        # 截取内容（避免太长）
        content = chapter.content[:3000] if len(chapter.content) > 3000 else chapter.content
        
        prompt = get_reverse_characters_prompt(novel.title, novel.genre, chapter.title, content, novel.summary or '')
        
        response = client.complete(prompt)
        
        # 解析JSON
        characters_data = parse_llm_json_response(response, default=[])
        
        # 保存到数据库
        created_count = 0
        for char_data in characters_data:
            if not isinstance(char_data, dict):
                continue
            
            char_name = char_data.get('name', '').strip()
            if not char_name:
                continue
            
            # 检查是否已存在
            existing = Character.query.filter_by(
                novel_id=novel.id,
                name=char_name
            ).first()
            
            if not existing:
                character = Character(
                    novel_id=novel.id,
                    name=char_name,
                    gender=char_data.get('gender', ''),
                    personality=char_data.get('personality', ''),
                    background=char_data.get('background', ''),
                    goal=char_data.get('goal', '')
                )
                db.session.add(character)
                created_count += 1
        
        # 关联角色到章节
        from ..models.models import ChapterCharacter
        for char_data in characters_data:
            if not isinstance(char_data, dict):
                continue
            char_name = char_data.get('name', '').strip()
            if char_name:
                character = Character.query.filter_by(novel_id=novel.id, name=char_name).first()
                if character:
                    # 检查是否已关联
                    existing_assoc = ChapterCharacter.query.filter_by(
                        chapter_id=chapter.id,
                        character_id=character.id
                    ).first()
                    if not existing_assoc:
                        assoc = ChapterCharacter(
                            chapter_id=chapter.id,
                            character_id=character.id
                        )
                        db.session.add(assoc)
        
        db.session.commit()
        
        return {
            'total_characters': len(characters_data),
            'created_count': created_count,
            'message': '角色反推成功'
        }
    except Exception as e:
        db.session.rollback()
        raise
