# v5/backend/app/routes/event_outlines.py
# 事件细纲API（流程B）

from flask import Blueprint, request
from ..models.models import db, Novel, EventOutline
from ..services.chapter_service import generate_event_chain, regenerate_single_event
from ..utils.response import success, error, created, not_found, bad_request, task_submitted
from ..utils.logger import get_logger
from .tasks import create_task

logger = get_logger(__name__)

event_outlines_bp = Blueprint('event_outlines', __name__)


@event_outlines_bp.route('/api/novels/<int:novel_id>/event-outlines/generate', methods=['POST'])
def generate_event_outlines(novel_id):
    """生成事件细纲"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        logger.info(f'开始生成事件链: novel_id={novel_id}')
        
        # 定义异步任务函数
        def generate_task():
            novel_obj = db.session.get(Novel, novel_id)
            if not novel_obj:
                raise ValueError('项目不存在')
            return generate_event_chain(novel_obj)
        
        task_id = create_task('generate_event_chain', novel_id, generate_task)
        
        logger.info(f'事件链生成任务已提交: task_id={task_id}')
        return task_submitted(task_id, '事件链生成任务已提交')
    except Exception as e:
        logger.error(f'提交事件链生成任务失败: {e}')
        return error('提交事件链生成任务失败')


@event_outlines_bp.route('/api/novels/<int:novel_id>/event-outlines', methods=['GET'])
def list_event_outlines(novel_id):
    """获取事件细纲列表"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        events = EventOutline.query.filter_by(novel_id=novel_id)\
            .order_by(EventOutline.event_no).all()
        
        logger.info(f'获取事件列表: novel_id={novel_id}, count={len(events)}')
        return success([{
            'id': e.id,
            'event_no': e.event_no,
            'title': e.title,
            'description': e.description,
            'cause': e.cause,
            'effect': e.effect,
            'related_characters': e.related_characters
        } for e in events])
    except Exception as e:
        logger.error(f'获取事件列表失败: {e}')
        return error('获取事件列表失败')


@event_outlines_bp.route('/api/novels/<int:novel_id>/event-outlines', methods=['POST'])
def create_event_outline(novel_id):
    """手动创建事件"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        data = request.get_json()
        if not data:
            return bad_request('请求体不能为空')
        
        title = (data.get('title') or '').strip()
        if not title:
            return bad_request('事件标题不能为空')
        
        # 计算下一个事件编号
        max_event = EventOutline.query.filter_by(novel_id=novel_id)\
            .order_by(EventOutline.event_no.desc()).first()
        next_no = (max_event.event_no + 1) if max_event else 1
        
        event = EventOutline(
            novel_id=novel_id,
            event_no=next_no,
            title=title,
            description=data.get('description', ''),
            cause=data.get('cause', ''),
            effect=data.get('effect', ''),
            related_characters=data.get('related_characters', '')
        )
        db.session.add(event)
        db.session.flush()  # 获取 event.id
        
        # 处理章节关联
        chapter_ids = data.get('chapter_ids', [])
        if chapter_ids:
            from ..models.models import ChapterEventMapping
            for ch_id in chapter_ids:
                mapping = ChapterEventMapping(
                    chapter_id=ch_id,
                    event_id=event.id,
                    sort_order=0
                )
                db.session.add(mapping)
        
        db.session.commit()
        
        logger.info(f'手动创建事件成功: novel_id={novel_id}, event_no={next_no}, title={title}')
        return success({
            'id': event.id,
            'event_no': event.event_no,
            'title': event.title,
            'description': event.description,
            'cause': event.cause,
            'effect': event.effect,
            'related_characters': event.related_characters
        }, '事件创建成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f'手动创建事件失败: {e}', exc_info=True)
        return error(f'创建事件失败: {str(e)}')


@event_outlines_bp.route('/api/novels/<int:novel_id>/event-outlines/<int:ev_no>', methods=['GET'])
def get_event_outline(novel_id, ev_no):
    """获取单个事件"""
    try:
        event = EventOutline.query.filter_by(novel_id=novel_id, event_no=ev_no).first()
        if not event:
            return not_found('事件不存在')
        
        logger.info(f'获取单个事件: novel_id={novel_id}, event_no={ev_no}')
        
        # 获取关联的章节
        from ..models.models import ChapterEventMapping, Chapter
        mappings = ChapterEventMapping.query.filter_by(event_id=event.id).all()
        chapter_ids = [m.chapter_id for m in mappings]
        
        return success({
            'id': event.id,
            'event_no': event.event_no,
            'title': event.title,
            'description': event.description,
            'cause': event.cause,
            'effect': event.effect,
            'related_characters': event.related_characters,
            'chapter_ids': chapter_ids
        })
    except Exception as e:
        logger.error(f'获取单个事件失败: {e}')
        return error('获取单个事件失败')


@event_outlines_bp.route('/api/novels/<int:novel_id>/event-outlines/<int:ev_no>', methods=['PUT'])
def update_event_outline(novel_id, ev_no):
    """更新事件"""
    try:
        event = EventOutline.query.filter_by(novel_id=novel_id, event_no=ev_no).first()
        if not event:
            return not_found('事件不存在')
        
        data = request.get_json()
        
        if 'title' in data:
            event.title = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'cause' in data:
            event.cause = data['cause']
        if 'effect' in data:
            event.effect = data['effect']
        if 'related_characters' in data:
            event.related_characters = data['related_characters']
        
        # 处理章节关联
        if 'chapter_ids' in data:
            from ..models.models import ChapterEventMapping
            ChapterEventMapping.query.filter_by(event_id=event.id).delete()
            for ch_id in data['chapter_ids']:
                mapping = ChapterEventMapping(
                    chapter_id=ch_id,
                    event_id=event.id,
                    sort_order=0
                )
                db.session.add(mapping)
        
        db.session.commit()
        
        logger.info(f'事件更新成功: novel_id={novel_id}, event_no={ev_no}')
        return success(message='事件更新成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新事件失败: {e}')
        return error('更新事件失败')


@event_outlines_bp.route('/api/novels/<int:novel_id>/event-outlines/<int:ev_no>', methods=['DELETE'])
def delete_event_outline(novel_id, ev_no):
    """删除事件"""
    try:
        event = EventOutline.query.filter_by(novel_id=novel_id, event_no=ev_no).first()
        if not event:
            return not_found('事件不存在')
        
        db.session.delete(event)
        db.session.commit()
        
        logger.info(f'事件删除成功: novel_id={novel_id}, event_no={ev_no}')
        return success(message='事件删除成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除事件失败: {e}')
        return error('删除事件失败')


@event_outlines_bp.route('/api/novels/<int:novel_id>/event-outlines/<int:ev_no>/regenerate', methods=['POST'])
def regenerate_event_outline(novel_id, ev_no):
    """重新生成事件"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        logger.info(f'开始重新生成事件: novel_id={novel_id}, event_no={ev_no}')
        
        # 定义异步任务函数
        def regenerate_task():
            novel_obj = db.session.get(Novel, novel_id)
            if not novel_obj:
                raise ValueError('项目不存在')
            return regenerate_single_event(novel_obj, ev_no)
        
        task_id = create_task('regenerate_event', novel_id, regenerate_task)
        
        logger.info(f'事件重新生成任务已提交: task_id={task_id}, event_no={ev_no}')
        return task_submitted(task_id, '事件重新生成任务已提交')
    except Exception as e:
        logger.error(f'提交事件重新生成任务失败: {e}')
        return error('提交事件重新生成任务失败')


@event_outlines_bp.route('/api/novels/<int:novel_id>/event-outlines/reorder', methods=['PUT'])
def reorder_event_outlines(novel_id):
    """批量更新事件顺序"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        data = request.get_json()
        event_ids = data.get('event_ids', [])
        
        # 更新事件序号
        for order, event_id in enumerate(event_ids):
            event = EventOutline.query.get(event_id)
            if event and event.novel_id == novel_id:
                event.event_no = order + 1
        
        db.session.commit()
        
        logger.info(f'事件顺序更新成功: novel_id={novel_id}, count={len(event_ids)}')
        return success(message='事件顺序更新成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新事件顺序失败: {e}')
        return error('更新事件顺序失败')


# ===== 全局事件对话接口 =====

@event_outlines_bp.route('/api/novels/<int:novel_id>/event-outlines/chat', methods=['POST'])
def chat_event_dialogue(novel_id):
    """事件对话迭代（同步）— 全局事件池"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return bad_request('消息不能为空')
        
        from ..services.outline_service import (
            get_event_chat_system_prompt, save_chat_message, get_chat_messages_raw
        )
        
        history = get_chat_messages_raw(novel_id, context_type='event')
        
        client = get_llm_client_ev()
        sys_prompt = get_event_chat_system_prompt(novel)
        llm_messages = [{"role": "system", "content": sys_prompt}]
        llm_messages.extend(history)
        llm_messages.append({"role": "user", "content": message})
        
        ai_response = client.chat(llm_messages)
        
        save_chat_message(novel_id, 'user', message, context_type='event')
        save_chat_message(novel_id, 'assistant', ai_response, context_type='event')
        
        return success({'response': ai_response})
    except Exception as e:
        logger.error(f'事件对话失败: {e}', exc_info=True)
        return error(f'事件对话失败: {str(e)}')


@event_outlines_bp.route('/api/novels/<int:novel_id>/event-outlines/chat/stream', methods=['POST'])
def chat_event_dialogue_stream(novel_id):
    """事件对话迭代（流式SSE）— 全局事件池"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        data = request.get_json(force=True, silent=True)
        if not data:
            raw = request.get_data(as_text=True)[:200]
            logger.warning(f'事件对话流式: 无法解析JSON, raw_body={raw}')
            return bad_request('请求体不能为空或不是有效JSON')
        
        message = (data.get('message') or '').strip()
        if not message:
            return bad_request('消息不能为空')
        
        from ..services.outline_service import get_event_chat_system_prompt, save_chat_message, get_chat_messages_raw
        import json as _json
        
        history = get_chat_messages_raw(novel_id, context_type='event')
        
        def generate():
            full = ""
            try:
                yield f"data: {_json.dumps({'type': 'user_sent', 'content': message})}\n\n"
                
                client = get_llm_client_ev()
                sys_prompt = get_event_chat_system_prompt(novel)
                llm_messages = [{"role": "system", "content": sys_prompt}]
                llm_messages.extend(history)
                llm_messages.append({"role": "user", "content": message})
                
                for chunk in client.stream_chat(llm_messages):
                    full += chunk
                    yield f"data: {_json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                
                save_chat_message(novel_id, 'user', message, context_type='event')
                save_chat_message(novel_id, 'assistant', full, context_type='event')
                yield f"data: {_json.dumps({'type': 'done'})}\n\n"
            except Exception as e:
                logger.error(f'事件对话流式生成失败: {e}')
                yield f"data: {_json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        
        from flask import Response, stream_with_context
        return Response(stream_with_context(generate()), mimetype='text/event-stream',
                        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
    except Exception as e:
        logger.error(f'事件对话流式请求异常: {e}', exc_info=True)
        return error(f'事件对话请求失败: {str(e)}')


@event_outlines_bp.route('/api/novels/<int:novel_id>/event-outlines/chat/accept', methods=['POST'])
def accept_event_dialogue(novel_id):
    """采纳事件对话，编译为全局事件列表"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        from ..services.outline_service import compile_events_from_chat, clear_chat_messages
        
        result = compile_events_from_chat(novel)
        clear_chat_messages(novel_id, context_type='event')
        
        logger.info(f'全局事件编译成功: novel_id={novel_id}, count={result["count"]}')
        return success(data=result, message=result['message'])
    except Exception as e:
        logger.error(f'编译事件失败: {e}', exc_info=True)
        return error(f'编译事件失败: {str(e)}')


@event_outlines_bp.route('/api/novels/<int:novel_id>/event-outlines/chat-history', methods=['GET'])
def get_event_chat_history(novel_id):
    """获取全局事件对话历史"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        from ..services.outline_service import get_chat_messages
        history = get_chat_messages(novel_id, context_type='event')
        return success(history)
    except Exception as e:
        logger.error(f'获取事件对话历史失败: {e}')
        return error('获取事件对话历史失败')


def get_llm_client_ev():
    """获取LLM客户端（与事件服务共用）"""
    from ..services.outline_service import get_llm_client
    return get_llm_client()
