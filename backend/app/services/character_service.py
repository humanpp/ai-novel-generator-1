# v5/backend/app/services/character_service.py
# 角色服务

from flask import current_app
from ..prompts import get_extract_characters_prompt, get_character_logic_chains_prompt
from ..models.models import db, Novel, Character
from ..llm.client import LLMClient
from ..utils.encryption import decrypt_api_key
from ..utils.json_parser import parse_llm_json_response
from .model_service import get_default_model
import json


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


def extract_characters_from_outline(novel):
    """从大纲/细纲/章节内容抽取角色"""
    try:
        client = get_llm_client()
        
        # 获取大纲内容
        outline_content = novel.outline.content if novel.outline else ''
        
        # 获取章节内容和细纲
        from ..models.models import Chapter, ChapterOutline, EventOutline
        
        chapters_content = ''
        outlines_content = ''
        
        if novel.workflow_mode == 'chapter':
            # 流程A：使用章节细纲和章节正文
            outlines = ChapterOutline.query.filter_by(novel_id=novel.id).all()
            outlines_content = '\n'.join([f"第{o.chapter_no}章细纲: {o.content}" for o in outlines if o.content])
            
            chapters = Chapter.query.filter_by(novel_id=novel.id).all()
            chapters_content = '\n'.join([f"第{c.chapter_no}章正文: {c.content[:2000] if c.content else '暂无'}" for c in chapters])
        else:
            # 流程B：使用事件链
            events = EventOutline.query.filter_by(novel_id=novel.id).all()
            outlines_content = '\n'.join([f"事件{e.event_no}: {e.title} - {e.description}" for e in events if e.description])
            
            chapters = Chapter.query.filter_by(novel_id=novel.id).all()
            chapters_content = '\n'.join([f"第{c.chapter_no}章正文: {c.content[:2000] if c.content else '暂无'}" for c in chapters])
        
        prompt = get_extract_characters_prompt(novel.title, novel.genre, outline_content, outlines_content, chapters_content, novel.summary or '')
        
        response = client.complete(prompt)
        
        # 使用改进的JSON解析器
        characters_data = parse_llm_json_response(response, default=[])
        
        if not characters_data:
            current_app.logger.warning(f"LLM响应解析失败，原始响应: {response[:500]}")
        
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
                # 处理relations字段
                relations = char_data.get('relations', [])
                if isinstance(relations, list):
                    relations_json = json.dumps(relations, ensure_ascii=False)
                else:
                    relations_json = '[]'
                
                character = Character(
                    novel_id=novel.id,
                    name=char_name,
                    gender=char_data.get('gender', ''),
                    personality=char_data.get('personality', ''),
                    background=char_data.get('background', ''),
                    goal=char_data.get('goal', ''),
                    relations=relations_json
                )
                db.session.add(character)
                created_count += 1
        
        db.session.commit()
        
        return {
            'total_characters': len(characters_data),
            'created_count': created_count,
            'message': '角色抽取成功'
        }
    except Exception as e:
        db.session.rollback()
        raise


def generate_character_logic_chains(novel):
    """生成角色逻辑链（通用，流程A/流程B自动适配数据源）"""
    try:
        client = get_llm_client()
        
        outline_content = novel.outline.content if novel.outline else ''
        
        characters = Character.query.filter_by(novel_id=novel.id).all()
        if not characters:
            return {'message': '没有角色，请先抽取角色'}
        
        # 根据工作流模式获取数据源和格式化
        is_event_mode = novel.workflow_mode == 'event'
        
        if is_event_mode:
            from ..models.models import EventOutline
            events = EventOutline.query.filter_by(novel_id=novel.id)\
                .order_by(EventOutline.event_no).all()
            unit_name = '事件'
            detail_lines = []
            for e in events:
                detail_lines.append(
                    f"[{unit_name}{e.event_no}] {e.title}\n"
                    f"  描述: {e.description or '无'}\n"
                    f"  前因: {e.cause or '无'}\n"
                    f"  后果: {e.effect or '无'}"
                )
            detail_content = '\n\n'.join(detail_lines) if detail_lines else '暂无事件'
        else:
            from ..models.models import ChapterOutline
            outlines = ChapterOutline.query.filter_by(novel_id=novel.id).all()
            unit_name = '章节'
            detail_lines = [f"第{o.chapter_no}章: {o.content}" for o in outlines if o.content]
            detail_content = '\n'.join(detail_lines) if detail_lines else '暂无细纲'
        
        characters_info = '\n'.join([
            f"- {c.name}: {c.personality or '未知性格'}, 背景: {c.background or '无'}, 目标: {c.goal or '无'}"
            for c in characters
        ])
        
        mode_hint = (
            "注意：这是事件驱动模式，chapter_no字段填写对应的事件序号(event_no)。"
            "每个角色在每个事件中都应有动机和变化描述。"
            "动机要体现该事件中的因果关系——角色因为什么原因做了什么事。"
            "变化要体现事件对角色造成的影响。"
        ) if is_event_mode else (
            "注意：这是章节细纲模式，chapter_no字段填写对应的章节序号。"
            "每个角色在每个章节中都应有动机和变化描述。"
        )
        
        prompt = get_character_logic_chains_prompt(novel.title, novel.genre, outline_content, unit_name, detail_content, characters_info, mode_hint, novel.summary or '')
        
        response = client.complete(prompt)
        
        logic_data = parse_llm_json_response(response, default=[])
        
        if not logic_data:
            current_app.logger.warning(f"LLM响应解析失败，原始响应: {response[:500]}")
        
        char_map = {c.name: c.id for c in characters}
        
        # 清空旧逻辑链
        from ..models.models import CharacterLogicChain
        CharacterLogicChain.query.filter_by(novel_id=novel.id).delete()
        db.session.flush()
        
        created_count = 0
        for item in logic_data:
            if not isinstance(item, dict):
                continue
            char_name = item.get('character_name')
            if char_name in char_map:
                logic = CharacterLogicChain(
                    novel_id=novel.id,
                    character_id=char_map[char_name],
                    chapter_no=item.get('chapter_no'),
                    motivation=item.get('motivation', ''),
                    change=item.get('change', ''),
                    content=f"动机: {item.get('motivation', '')}\n变化: {item.get('change', '')}"
                )
                db.session.add(logic)
                created_count += 1
        
        db.session.commit()
        
        return {
            'total_items': len(logic_data),
            'created_count': created_count,
            'message': '角色逻辑链生成成功',
            'mode': novel.workflow_mode
        }
    except Exception as e:
        db.session.rollback()
        raise


def generate_mindmap_data(novel):
    """生成脑图数据"""
    try:
        characters = Character.query.filter_by(novel_id=novel.id).all()
        
        nodes = []
        links = []
        
        for char in characters:
            # 添加节点
            nodes.append({
                'id': str(char.id),
                'name': char.name,
                'gender': char.gender,
                'personality': char.personality[:50] if char.personality else ''
            })
            
            # 解析关系
            if char.relations:
                try:
                    relations = json.loads(char.relations)
                    for rel in relations:
                        target_name = rel.get('target')
                        # 查找目标角色
                        target_char = Character.query.filter_by(
                            novel_id=novel.id,
                            name=target_name
                        ).first()
                        
                        if target_char:
                            links.append({
                                'source': str(char.id),
                                'target': str(target_char.id),
                                'relation': rel.get('relation', '')
                            })
                except json.JSONDecodeError:
                    pass
        
        return {
            'nodes': nodes,
            'links': links
        }
    except Exception as e:
        raise


def build_chapter_event_mindmap(novel):
    """构建章节-事件脑图数据（章节=节点，事件=节点，连线=映射关系）
    
    Returns:
        dict: { nodes: [...], links: [...] }
    """
    from ..models.models import Chapter, EventOutline, ChapterEventMapping
    
    chapters = Chapter.query.filter_by(novel_id=novel.id)\
        .order_by(Chapter.chapter_no).all()
    events = EventOutline.query.filter_by(novel_id=novel.id)\
        .order_by(EventOutline.event_no).all()
    
    # 构建映射: { chapter_id: [mapping, ...] }
    all_mappings = ChapterEventMapping.query\
        .join(Chapter, ChapterEventMapping.chapter_id == Chapter.id)\
        .filter(Chapter.novel_id == novel.id)\
        .order_by(ChapterEventMapping.sort_order).all()
    
    nodes = []
    links = []
    
    # 章节节点
    for ch in chapters:
        nodes.append({
            'id': f'ch_{ch.id}',
            'name': ch.title or f'第{ch.chapter_no}章',
            'type': 'chapter',
            'chapter_no': ch.chapter_no,
            'word_count': ch.word_count or 0,
            'has_content': bool(ch.content)
        })
    
    # 事件节点
    for ev in events:
        nodes.append({
            'id': f'ev_{ev.id}',
            'name': ev.title or f'事件{ev.event_no}',
            'type': 'event',
            'event_no': ev.event_no,
            'description': ev.description[:80] if ev.description else '',
            'cause': ev.cause[:50] if ev.cause else '',
            'effect': ev.effect[:50] if ev.effect else ''
        })
    
    # 连线
    for m in all_mappings:
        links.append({
            'source': f'ev_{m.event_id}',
            'target': f'ch_{m.chapter_id}',
            'mapping_id': m.id,
            'sort_order': m.sort_order
        })
    
    return {
        'nodes': nodes,
        'links': links,
        'chapter_count': len(chapters),
        'event_count': len(events),
        'link_count': len(links)
    }


def update_chapter_event_links(novel, links):
    """批量更新章节-事件连线
    
    Args:
        novel: Novel对象
        links: [{event_id, chapter_id, sort_order}, ...]
    
    Returns:
        dict: {created_count, message}
    """
    from ..models.models import Chapter, EventOutline, ChapterEventMapping
    
    # 验证所有章节和事件属于当前项目
    chapter_ids = {ch.id for ch in Chapter.query.filter_by(novel_id=novel.id).all()}
    event_ids = {ev.id for ev in EventOutline.query.filter_by(novel_id=novel.id).all()}
    
    # 清除该项目的所有现有映射
    chapter_ids_for_delete = Chapter.query.with_entities(Chapter.id)\
        .filter_by(novel_id=novel.id).all()
    chapter_id_list = [c[0] for c in chapter_ids_for_delete]
    if chapter_id_list:
        ChapterEventMapping.query\
            .filter(ChapterEventMapping.chapter_id.in_(chapter_id_list))\
            .delete(synchronize_session='fetch')
        db.session.flush()
    
    created_count = 0
    for link in links:
        event_id = link.get('event_id')
        chapter_id = link.get('chapter_id')
        sort_order = link.get('sort_order', 0)
        
        if not event_id or not chapter_id:
            continue
        if event_id not in event_ids or chapter_id not in chapter_ids:
            continue
        
        mapping = ChapterEventMapping(
            chapter_id=chapter_id,
            event_id=event_id,
            sort_order=sort_order
        )
        db.session.add(mapping)
        created_count += 1
    
    db.session.commit()
    
    return {
        'created_count': created_count,
        'message': f'已更新 {created_count} 条连线'
    }
