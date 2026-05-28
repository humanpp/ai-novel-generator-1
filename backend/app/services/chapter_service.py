# v5/backend/app/services/chapter_service.py
# 章节服务

from flask import current_app
from ..models.models import (
    db, Novel, Chapter, ChapterOutline, EventOutline,
    ChapterVersion, ChapterEventMapping, CharacterLogicChain
)
from ..llm.client import LLMClient
from ..utils.encryption import decrypt_api_key
from ..utils.json_parser import parse_llm_json_response
from .model_service import get_default_model
from ..prompts import (
    get_chapter_outlines_prompt,
    get_single_chapter_outline_prompt,
    get_regenerate_single_outline_prompt,
    get_event_chain_system_prompt,
    get_event_chain_generation_extra,
    get_regenerate_event_prompt,
    get_chapter_content_chapter_mode_prompt,
    get_chapter_content_event_mode_prompt,
)


def get_llm_client():
    """获取LLM客户端"""
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


def generate_chapter_outlines(novel, params):
    """生成章节细纲（流程A）"""
    try:
        total_chapters = params.get('total_chapters', 10)
        word_count_per_chapter = params.get('word_count_per_chapter', 3000)
        
        client = get_llm_client()
        
        # 获取大纲内容
        outline_content = novel.outline.content if novel.outline else ''
        
        prompt = get_chapter_outlines_prompt(novel.title, novel.genre, outline_content, total_chapters, word_count_per_chapter, novel.summary or '')
        
        response = client.complete(prompt)
        
        # 使用改进的JSON解析器
        chapters_data = parse_llm_json_response(response, default=[])
        
        if not chapters_data:
            current_app.logger.warning(f"LLM响应解析失败，原始响应: {response[:500]}")
        
        # 保存到数据库
        for ch_data in chapters_data:
            if not isinstance(ch_data, dict):
                continue
            outline = ChapterOutline(
                novel_id=novel.id,
                chapter_no=ch_data.get('chapter_no'),
                word_count=ch_data.get('word_count', word_count_per_chapter),
                content=ch_data.get('content', '')
            )
            db.session.add(outline)
        
        db.session.commit()
        
        return {
            'total_chapters': len(chapters_data),
            'message': '章节细纲生成成功'
        }
    except Exception as e:
        db.session.rollback()
        raise


def generate_single_chapter_outline(novel, chapter_no):
    """生成单章细纲（需要先有章节）"""
    try:
        client = get_llm_client()
        
        # 获取大纲内容
        outline_content = novel.outline.content if novel.outline else ''
        
        # 获取章节信息
        chapter = Chapter.query.filter_by(novel_id=novel.id, chapter_no=chapter_no).first()
        if not chapter:
            raise ValueError(f'章节{chapter_no}不存在')
        
        # 获取前后章节细纲（用于保持连贯性）
        prev_outline = ChapterOutline.query.filter_by(
            novel_id=novel.id, chapter_no=chapter_no - 1
        ).first()
        next_outline = ChapterOutline.query.filter_by(
            novel_id=novel.id, chapter_no=chapter_no + 1
        ).first()
        
        prompt = get_single_chapter_outline_prompt(novel.title, novel.genre, outline_content, chapter_no, chapter.title,
            prev_outline.content if prev_outline else '',
            next_outline.content if next_outline else '',
            novel.summary or '')
        
        response = client.complete(prompt)
        
        # 更新或创建章节细纲
        outline = ChapterOutline.query.filter_by(
            novel_id=novel.id, chapter_no=chapter_no
        ).first()
        
        if outline:
            outline.content = response
            outline.word_count = len(response)
        else:
            outline = ChapterOutline(
                novel_id=novel.id,
                chapter_no=chapter_no,
                content=response,
                word_count=len(response)
            )
            db.session.add(outline)
        
        db.session.commit()
        
        return {
            'chapter_no': chapter_no,
            'content': response,
            'word_count': len(response),
            'message': '章节细纲生成成功'
        }
    except Exception as e:
        db.session.rollback()
        raise


def regenerate_single_outline(novel, chapter_no):
    """重新生成单章细纲"""
    try:
        client = get_llm_client()
        
        # 获取大纲和相邻章节
        outline_content = novel.outline.content if novel.outline else ''
        
        # 获取前后章节
        prev_outline = ChapterOutline.query.filter_by(
            novel_id=novel.id, chapter_no=chapter_no - 1
        ).first()
        next_outline = ChapterOutline.query.filter_by(
            novel_id=novel.id, chapter_no=chapter_no + 1
        ).first()
        
        prompt = get_regenerate_single_outline_prompt(novel.title, novel.genre, outline_content, chapter_no,
            prev_outline.content if prev_outline else '',
            next_outline.content if next_outline else '',
            novel.summary or '')
        
        response = client.complete(prompt)
        
        # 更新或创建
        outline = ChapterOutline.query.filter_by(
            novel_id=novel.id, chapter_no=chapter_no
        ).first()
        
        if outline:
            outline.content = response
        else:
            outline = ChapterOutline(
                novel_id=novel.id,
                chapter_no=chapter_no,
                content=response
            )
            db.session.add(outline)
        
        db.session.commit()
        
        return {
            'chapter_no': chapter_no,
            'content': response,
            'message': '章节细纲重新生成成功'
        }
    except Exception as e:
        db.session.rollback()
        raise


def _build_event_chain_prompt(outline_content, genre='', title='', summary=''):
    """构建事件链生成的增强系统提示词"""
    return get_event_chain_system_prompt(title, genre, summary)


def generate_event_chain(novel):
    """生成事件链（流程B）"""
    try:
        client = get_llm_client()
        
        outline_content = novel.outline.content if novel.outline else ''
        
        prompt = _build_event_chain_prompt(outline_content, novel.genre or '', novel.title, novel.summary or '') + get_event_chain_generation_extra(novel.title, novel.genre, outline_content, novel.format, novel.summary or '')

        response = client.complete(prompt)
        
        events_data = parse_llm_json_response(response, default=[])
        
        if not events_data:
            current_app.logger.warning(f"LLM响应解析失败，原始响应: {response[:500]}")
        
        # 清空旧事件
        EventOutline.query.filter_by(novel_id=novel.id).delete()
        db.session.flush()
        
        # 保存到数据库
        for ev_data in events_data:
            if not isinstance(ev_data, dict):
                continue
            event = EventOutline(
                novel_id=novel.id,
                event_no=ev_data.get('event_no', len(events_data)),
                title=ev_data.get('title', ''),
                description=ev_data.get('description', ''),
                cause=ev_data.get('cause', ''),
                effect=ev_data.get('effect', ''),
                related_characters=ev_data.get('related_characters', '')
            )
            db.session.add(event)
        
        db.session.commit()
        
        return {
            'total_events': len(events_data),
            'message': '事件链生成成功'
        }
    except Exception as e:
        db.session.rollback()
        raise


def regenerate_single_event(novel, event_no):
    """重新生成单个事件"""
    try:
        client = get_llm_client()
        
        # 获取大纲内容
        outline_content = novel.outline.content if novel.outline else ''
        
        # 获取相邻事件
        prev_event = EventOutline.query.filter_by(
            novel_id=novel.id, event_no=event_no - 1
        ).first()
        next_event = EventOutline.query.filter_by(
            novel_id=novel.id, event_no=event_no + 1
        ).first()
        
        # 获取当前事件
        current_event = EventOutline.query.filter_by(
            novel_id=novel.id, event_no=event_no
        ).first()
        
        prev_info = f"事件：{prev_event.title}\n{prev_event.description}" if prev_event else ''
        next_info = f"事件：{next_event.title}\n{next_event.description}" if next_event else ''
        curr_info = f"标题：{current_event.title}\n描述：{current_event.description}" if current_event else ''
        prompt = get_regenerate_event_prompt(novel.title, novel.genre, outline_content, event_no, prev_info, next_info, curr_info, novel.summary or '')
        
        response = client.complete(prompt)
        
        import json
        try:
            event_data = json.loads(response)
        except json.JSONDecodeError as e:
            current_app.logger.warning(f"LLM响应JSON解析失败: {e}")
            event_data = {
                'title': f'事件 {event_no}',
                'description': response,
                'cause': '',
                'effect': '',
                'related_characters': ''
            }
        
        # 更新或创建事件
        if current_event:
            current_event.title = event_data.get('title', current_event.title)
            current_event.description = event_data.get('description', current_event.description)
            current_event.cause = event_data.get('cause', current_event.cause)
            current_event.effect = event_data.get('effect', current_event.effect)
            current_event.related_characters = event_data.get('related_characters', current_event.related_characters)
        else:
            current_event = EventOutline(
                novel_id=novel.id,
                event_no=event_no,
                title=event_data.get('title', ''),
                description=event_data.get('description', ''),
                cause=event_data.get('cause', ''),
                effect=event_data.get('effect', ''),
                related_characters=event_data.get('related_characters', '')
            )
            db.session.add(current_event)
        
        db.session.commit()
        
        return {
            'event_no': event_no,
            'title': current_event.title,
            'description': current_event.description,
            'message': '事件重新生成成功'
        }
    except Exception as e:
        db.session.rollback()
        raise


def auto_map_events_to_chapters(novel):
    """自动映射事件到章节（全局）"""
    try:
        events = EventOutline.query.filter_by(novel_id=novel.id)\
            .order_by(EventOutline.event_no).all()
        
        if not events:
            return {'message': '没有事件可映射'}
        
        # 获取或创建章节
        chapters = Chapter.query.filter_by(novel_id=novel.id)\
            .order_by(Chapter.chapter_no).all()
        
        # 如果没有章节，根据事件数量创建
        if not chapters:
            chapter_count = max(1, len(events) // 2)
            for i in range(1, chapter_count + 1):
                chapter = Chapter(
                    novel_id=novel.id,
                    chapter_no=i,
                    title=f'第{i}章'
                )
                db.session.add(chapter)
            db.session.flush()
            chapters = Chapter.query.filter_by(novel_id=novel.id)\
                .order_by(Chapter.chapter_no).all()
        
        # 清除现有映射
        for chapter in chapters:
            ChapterEventMapping.query.filter_by(chapter_id=chapter.id).delete()
        
        # 平均分配事件到章节
        events_per_chapter = len(events) / len(chapters)
        for i, event in enumerate(events):
            chapter_idx = int(i / events_per_chapter)
            chapter_idx = min(chapter_idx, len(chapters) - 1)
            
            mapping = ChapterEventMapping(
                chapter_id=chapters[chapter_idx].id,
                event_id=event.id,
                sort_order=i
            )
            db.session.add(mapping)
        
        db.session.commit()
        
        return {
            'chapters_count': len(chapters),
            'events_count': len(events),
            'message': '事件映射完成'
        }
    except Exception as e:
        db.session.rollback()
        raise


def auto_map_events_for_chapter(novel_id, chapter):
    """对单个章节重新执行事件映射"""
    try:
        # 获取所有事件
        all_events = EventOutline.query.filter_by(novel_id=novel_id)\
            .order_by(EventOutline.event_no).all()
        
        # 获取所有章节
        all_chapters = Chapter.query.filter_by(novel_id=novel_id)\
            .order_by(Chapter.chapter_no).all()
        
        if not all_events:
            return {'message': '没有事件可映射'}
        
        chapter_idx = all_chapters.index(chapter) if chapter in all_chapters else 0
        
        # 清除该章节现有映射
        ChapterEventMapping.query.filter_by(chapter_id=chapter.id).delete()
        
        # 按比例分配给该章节的事件
        events_per_chapter = max(1, len(all_events) / max(1, len(all_chapters)))
        start_idx = int(chapter_idx * events_per_chapter)
        end_idx = int(min(start_idx + events_per_chapter, len(all_events)))
        
        assigned_count = 0
        for i, event in enumerate(all_events[start_idx:end_idx]):
            mapping = ChapterEventMapping(
                chapter_id=chapter.id,
                event_id=event.id,
                sort_order=i
            )
            db.session.add(mapping)
            assigned_count += 1
        
        db.session.commit()
        
        return {
            'chapter_no': chapter.chapter_no,
            'assigned_count': assigned_count,
            'message': f'已为该章映射 {assigned_count} 个事件'
        }
    except Exception as e:
        db.session.rollback()
        raise


def generate_chapter_content(novel, chapter_no):
    """生成章节正文"""
    try:
        client = get_llm_client()
        
        # 获取大纲
        outline_content = novel.outline.content if novel.outline else ''
        
        # 获取上一章正文（用于连贯性）
        prev_chapter = Chapter.query.filter_by(
            novel_id=novel.id, chapter_no=chapter_no - 1
        ).first()
        prev_content = prev_chapter.content if prev_chapter else ''
        # 如果上一章内容过长，取末尾部分保持上下文连贯
        if len(prev_content) > 2000:
            prev_content = '...(前文省略)...\n' + prev_content[-2000:]
        
        # 获取章节细纲或事件
        if novel.workflow_mode == 'chapter':
            # 流程A：使用章节细纲
            chapter_outline = ChapterOutline.query.filter_by(
                novel_id=novel.id, chapter_no=chapter_no
            ).first()
            detail_content = chapter_outline.content if chapter_outline else ''
            detail_label = '章节细纲'
        else:
            # 流程B：使用事件映射，包含完整事件信息
            chapter = Chapter.query.filter_by(
                novel_id=novel.id, chapter_no=chapter_no
            ).first()
            
            if chapter:
                mappings = ChapterEventMapping.query.filter_by(
                    chapter_id=chapter.id
                ).order_by(ChapterEventMapping.sort_order).all()
                
                events = []
                for m in mappings:
                    event = EventOutline.query.get(m.event_id)
                    if event:
                        events.append(
                            f"事件{m.event_no}：{event.title}\n"
                            f"描述：{event.description}\n"
                            f"前因：{event.cause}\n"
                            f"后果：{event.effect}\n"
                            f"关联角色：{event.related_characters}"
                        )
                detail_content = '\n\n'.join(events)
            else:
                detail_content = ''
            detail_label = '本章需覆盖的事件链'
        
        # 获取角色逻辑链
        logic_chains = CharacterLogicChain.query.filter_by(
            novel_id=novel.id, chapter_no=chapter_no
        ).all()
        
        logic_content = ''
        for lc in logic_chains:
            logic_content += f"\n角色{lc.character_id}: 动机={lc.motivation}, 变化={lc.change}"
        
        # 构建提示词，区分工作流A和工作流B
        if novel.workflow_mode == 'chapter':
            prompt = get_chapter_content_chapter_mode_prompt(novel.title, novel.genre, outline_content, detail_content, prev_content, logic_content, chapter_no, novel.summary or '')
        else:
            prompt = get_chapter_content_event_mode_prompt(novel.title, novel.genre, outline_content, detail_content, prev_content, logic_content, chapter_no, novel.summary or '')
        
        content = client.complete(prompt)
        
        # 保存或更新章节
        chapter = Chapter.query.filter_by(
            novel_id=novel.id, chapter_no=chapter_no
        ).first()
        
        if not chapter:
            chapter = Chapter(
                novel_id=novel.id,
                chapter_no=chapter_no,
                title=f'第{chapter_no}章',
                content=content,
                word_count=len(content)
            )
            db.session.add(chapter)
        else:
            # 保存旧版本
            if chapter.content:
                current_version = ChapterVersion.query.filter_by(
                    chapter_id=chapter.id
                ).order_by(ChapterVersion.version.desc()).first()
                
                new_version_num = (current_version.version + 1) if current_version else 1
                
                version = ChapterVersion(
                    chapter_id=chapter.id,
                    version=new_version_num,
                    content=chapter.content,
                    word_count=chapter.word_count
                )
                db.session.add(version)
            
            chapter.content = content
            chapter.word_count = len(content)
        
        db.session.commit()
        
        return {
            'chapter_no': chapter_no,
            'word_count': len(content),
            'message': '章节正文生成成功'
        }
    except Exception as e:
        db.session.rollback()
        raise


def batch_generate_chapters(novel, chapter_numbers):
    """批量生成章节"""
    from ..routes.tasks import create_task
    
    def generate_task():
        results = []
        for ch_no in chapter_numbers:
            try:
                result = generate_chapter_content(novel, ch_no)
                results.append(result)
            except Exception as e:
                results.append({
                    'chapter_no': ch_no,
                    'error': str(e)
                })
        return results
    
    task_id = create_task('batch_generate', novel.id, generate_task)
    
    return {
        'task_id': task_id,
        'chapter_count': len(chapter_numbers),
        'message': '批量生成任务已提交'
    }
