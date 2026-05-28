# -*- coding: utf-8 -*-
# v5/backend/app/services/outline_service.py
# 大纲服务 + 对话消息持久化

from flask import current_app
from ..models.models import db, Outline, OutlineVersion, ChatMessage
from ..llm.client import LLMClient
from ..utils.encryption import decrypt_api_key
from datetime import datetime

# Import prompt templates from the centralized prompts module
from ..prompts import (
    get_outline_dialogue_prompt,
    get_event_chat_prompt,
    get_compile_events_prompt,
    get_compile_outline_prompt as _compile_outline_prompt_data,
)


def get_llm_client():
    """获取LLM客户端"""
    from .model_service import get_default_model
    model = get_default_model()
    if not model:
        raise ValueError("未配置默认模型")
    
    # 解密API密钥
    api_key = decrypt_api_key(model.api_key) if model.api_key else ''
    
    config = {
        'base_url': model.base_url,
        'api_key': api_key,
        'model_name': model.model_name,
        'temperature': model.temperature,
        'max_tokens': model.max_tokens
    }
    return LLMClient(config)


def get_outline_system_prompt(title, genre, format_type, existing_outline=None, chapter_count=0, summary=''):
    """Wrapper: delegate to prompts.py for outline system prompts"""
    return get_outline_dialogue_prompt(title, genre, format_type, existing_outline, chapter_count, summary)


def _build_outline_system_prompt(novel):
    """构建带上下文的系统提示词（从novel对象提取上下文）"""
    existing_outline = None
    outline = Outline.query.filter_by(novel_id=novel.id).first()
    if outline and outline.content:
        existing_outline = outline.content
    
    from ..models.models import Chapter
    chapter_count = Chapter.query.filter_by(novel_id=novel.id).count()
    
    return get_outline_system_prompt(
        novel.title,
        novel.genre,
        novel.format,
        existing_outline=existing_outline,
        chapter_count=chapter_count,
        summary=novel.summary or ''
    )


def generate_outline_dialogue(novel, user_message, history_messages):
    """生成大纲对话（同步版本）"""
    try:
        client = get_llm_client()
        messages = [
            {"role": "system", "content": _build_outline_system_prompt(novel)}
        ]
        for msg in history_messages:
            messages.append(msg)
        messages.append({"role": "user", "content": user_message})
        response = client.chat(messages)
        return response
    except Exception as e:
        current_app.logger.error(f"生成大纲对话失败: {e}")
        raise


def generate_outline_dialogue_stream(novel, user_message, history_messages):
    """流式生成大纲对话 - 生成器"""
    try:
        client = get_llm_client()
        messages = [
            {"role": "system", "content": _build_outline_system_prompt(novel)}
        ]
        for msg in history_messages:
            messages.append(msg)
        messages.append({"role": "user", "content": user_message})
        full_response = ""
        for chunk in client.stream_chat(messages):
            full_response += chunk
            yield chunk
        # 生成结束后由调用方处理持久化
    except Exception as e:
        current_app.logger.error(f"流式生成大纲对话失败: {e}")
        yield f"\n\n[系统错误] {str(e)}"


def accept_outline_result(novel, accepted_content):
    """采纳大纲结果（直接写入内容）"""
    try:
        outline = Outline.query.filter_by(novel_id=novel.id).first()
        
        if not outline:
            # 创建新大纲
            outline = Outline(novel_id=novel.id, content=accepted_content, version=1)
            db.session.add(outline)
        else:
            # 保存当前版本
            if outline.content:
                version = OutlineVersion(
                    outline_id=outline.id,
                    version=outline.version,
                    content=outline.content
                )
                db.session.add(version)
            
            # 更新大纲
            outline.content = accepted_content
            outline.version += 1
        
        db.session.commit()
        return outline
    except Exception as e:
        db.session.rollback()
        raise


def compile_outline_from_chat(novel):
    """从整轮对话中编译提炼大纲
    
    将所有对话消息发送给LLM，要求其按 主旨/精神/主角经历 格式整理。
    """
    try:
        client = get_llm_client()
        
        # 获取所有对话消息
        messages = ChatMessage.query.filter_by(novel_id=novel.id)\
            .order_by(ChatMessage.created_at.asc()).all()
        
        if not messages:
            raise ValueError("没有对话历史，无法编译大纲")
        
        conversation = ""
        for msg in messages:
            role_label = "作者" if msg.role == "user" else "顾问" if msg.role == "assistant" else "系统"
            conversation += f"\n【{role_label}】: {msg.content}\n"
        
        outline = Outline.query.filter_by(novel_id=novel.id).first()
        outline_content = outline.content if outline else ''
        
        # 调用提示数据（从 prompts.py 获取）
        compile_prompt = _compile_outline_prompt_data(novel.title, novel.genre, novel.format, novel.summary or '')
        
        llm_messages = [
            {"role": "system", "content": compile_prompt},
            {"role": "user", "content": f"请将以下对话整理成大纲：\n\n{conversation}"}
        ]
        
        compiled = client.chat(llm_messages)
        
        # 保存编译后的大纲
        outline = Outline.query.filter_by(novel_id=novel.id).first()
        
        if not outline:
            outline = Outline(novel_id=novel.id, content=compiled, version=1)
            db.session.add(outline)
        else:
            if outline.content:
                version = OutlineVersion(
                    outline_id=outline.id,
                    version=outline.version,
                    content=outline.content
                )
                db.session.add(version)
            
            outline.content = compiled
            outline.version += 1
        
        db.session.commit()
        return {
            'outline': compiled,
            'version': outline.version,
            'message': '大纲编译成功'
        }
    except Exception as e:
        db.session.rollback()
        raise


def get_outline_content(novel):
    """获取大纲内容"""
    outline = Outline.query.filter_by(novel_id=novel.id).first()
    if outline:
        return {
            'id': outline.id,
            'content': outline.content,
            'version': outline.version
        }
    return None


def update_outline_content(novel, content):
    """更新大纲内容（手动编辑）"""
    try:
        outline = Outline.query.filter_by(novel_id=novel.id).first()
        
        if not outline:
            outline = Outline(novel_id=novel.id, content=content, version=1)
            db.session.add(outline)
        else:
            if outline.content:
                version = OutlineVersion(
                    outline_id=outline.id,
                    version=outline.version,
                    content=outline.content
                )
                db.session.add(version)
            
            outline.content = content
            outline.version += 1
        
        db.session.commit()
        return outline
    except Exception as e:
        db.session.rollback()
        raise


def get_outline_versions(novel):
    """获取大纲版本列表"""
    outline = Outline.query.filter_by(novel_id=novel.id).first()
    if not outline:
        return []
    
    versions = OutlineVersion.query.filter_by(outline_id=outline.id)\
        .order_by(OutlineVersion.version.desc()).all()
    
    # 添加当前版本
    result = [{
        'version': outline.version,
        'content': outline.content,
        'is_current': True,
        'created_at': None
    }]
    
    for v in versions:
        result.append({
            'version': v.version,
            'content': v.content,
            'is_current': False,
            'created_at': v.created_at.isoformat() if v.created_at else None
        })
    
    return result


def rollback_outline_version(novel, version_num):
    """回滚到指定版本"""
    try:
        outline = Outline.query.filter_by(novel_id=novel.id).first()
        if not outline:
            raise ValueError("大纲不存在")
        
        if outline.version == version_num:
            return outline
        
        if version_num < outline.version:
            version = OutlineVersion.query.filter_by(
                outline_id=outline.id,
                version=version_num
            ).first()
            if not version:
                raise ValueError(f"版本 {version_num} 不存在")
            current_version = OutlineVersion(
                outline_id=outline.id,
                version=outline.version,
                content=outline.content
            )
            db.session.add(current_version)
            outline.content = version.content
            outline.version = version_num
        else:
            raise ValueError("无效的版本号")
        
        db.session.commit()
        return outline
    except Exception as e:
        db.session.rollback()
        raise


# ===== 对话消息持久化 =====

def save_chat_message(novel_id, role, content, context_type='outline', chapter_no=None):
    """保存一条对话消息到数据库"""
    try:
        msg = ChatMessage(
            novel_id=novel_id,
            role=role,
            content=content,
            context_type=context_type,
            chapter_no=chapter_no
        )
        db.session.add(msg)
        db.session.commit()
        return msg
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"保存对话消息失败: {e}")
        raise


def get_chat_messages(novel_id, context_type=None, chapter_no=None, limit=None):
    """获取对话历史（按时间升序，可按上下文过滤）"""
    query = ChatMessage.query.filter_by(novel_id=novel_id)
    if context_type:
        query = query.filter_by(context_type=context_type)
    if chapter_no is not None:
        query = query.filter_by(chapter_no=chapter_no)
    query = query.order_by(ChatMessage.created_at.asc())
    if limit:
        query = query.limit(limit)
    messages = query.all()
    return [{ 'role': m.role, 'content': m.content, 'id': m.id, 'context_type': m.context_type, 'chapter_no': m.chapter_no, 'created_at': m.created_at.isoformat() if m.created_at else None } for m in messages]


def get_chat_messages_raw(novel_id, context_type=None, chapter_no=None):
    """获取对话历史的原始消息列表"""
    query = ChatMessage.query.filter_by(novel_id=novel_id)
    if context_type:
        query = query.filter_by(context_type=context_type)
    if chapter_no is not None:
        query = query.filter_by(chapter_no=chapter_no)
    messages = query.order_by(ChatMessage.created_at.asc()).all()
    return [{ 'role': m.role, 'content': m.content } for m in messages]


def clear_chat_messages(novel_id, context_type=None, chapter_no=None):
    """清空对话历史"""
    try:
        query = ChatMessage.query.filter_by(novel_id=novel_id)
        if context_type:
            query = query.filter_by(context_type=context_type)
        if chapter_no is not None:
            query = query.filter_by(chapter_no=chapter_no)
        query.delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"清空对话消息失败: {e}")
        raise


def delete_chat_message(msg_id):
    """删除单条消息"""
    try:
        msg = ChatMessage.query.get(msg_id)
        if msg:
            db.session.delete(msg)
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        raise


# ===== 事件对话系统（全局事件池）===== 

def get_event_chat_system_prompt(novel):
    """获取全局事件对话的系统提示词 — 事件独立于章节"""
    from ..models.models import Chapter, EventOutline
    
    outline = Outline.query.filter_by(novel_id=novel.id).first()
    outline_content = outline.content if outline else '暂无大纲'
    
    existing_events = EventOutline.query.filter_by(novel_id=novel.id)\
        .order_by(EventOutline.event_no).all()
    
    existing_text = ''
    if existing_events:
        lines = ['## 已有事件（确保新事件不重复、逻辑连贯）']
        for e in existing_events:
            lines.append(f"- 事件{e.event_no}『{e.title}』→ 后果：{e.effect or '（无）'}")
        existing_text = '\n'.join(lines)
    
    return get_event_chat_prompt(novel.title, novel.genre, outline_content, existing_text, novel.summary or '')


def compile_events_from_chat(novel):
    """从事件对话中编译全局事件列表（不绑定章节）"""
    try:
        client = get_llm_client()
        messages = ChatMessage.query.filter_by(
            novel_id=novel.id, context_type='event'
        ).order_by(ChatMessage.created_at.asc()).all()
        if not messages:
            raise ValueError("没有对话历史")
        conversation = ""
        for msg in messages:
            role_label = "作者" if msg.role == "user" else "顾问" if msg.role == "assistant" else "系统"
            conversation += f"\n【{role_label}】: {msg.content}\n"
        outline = Outline.query.filter_by(novel_id=novel.id).first()
        outline_content = outline.content if outline else ''
        from ..models.models import EventOutline as EO
        existing = EO.query.filter_by(novel_id=novel.id).order_by(EO.event_no).all()
        existing_text = ''
        if existing:
            existing_text = '已有事件（新事件将追加在后面，确保事件号不重复）：\n' + '\n'.join(
                [f"事件{e.event_no}『{e.title}』→ {e.effect}" for e in existing]
            )
        # 使用 prompts.py 提供的编译事件提示
        compile_prompt = get_compile_events_prompt(novel.title, novel.genre, outline_content, existing_text, novel.summary or '')
        compile_prompt += f"\n\n请将以下对话整理成事件链：\n\n{conversation}"
        response = client.complete(compile_prompt)
        from ..utils.json_parser import parse_llm_json_response
        events_data = parse_llm_json_response(response, default=[])
        if not events_data:
            return {'events': [], 'message': '解析失败，请重新对话'}
        max_no = EO.query.filter_by(novel_id=novel.id).order_by(EO.event_no.desc()).first()
        start_no = (max_no.event_no + 1) if max_no else 1
        created = []
        for i, ev in enumerate(events_data):
            if not isinstance(ev, dict):
                continue
            event_no = start_no + i
            event = EO(
                novel_id=novel.id,
                event_no=event_no,
                title=ev.get('title', f'事件{event_no}'),
                description=ev.get('description', ''),
                cause=ev.get('cause', ''),
                effect=ev.get('effect', ''),
                related_characters=ev.get('related_characters', '')
            )
            db.session.add(event)
            created.append({'event_no': event_no, 'title': event.title})
        db.session.commit()
        return {
            'events': created,
            'count': len(created),
            'message': f'已创建 {len(created)} 个事件（编号 {start_no}-{start_no + len(created) - 1}）'
        }
    except Exception as e:
        db.session.rollback()
        raise
