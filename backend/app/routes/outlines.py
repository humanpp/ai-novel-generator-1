# v5/backend/app/routes/outlines.py
# 大纲相关API

from flask import Blueprint, request, Response, stream_with_context
from ..models.models import db, Novel, Outline, OutlineVersion
from ..services.outline_service import (
    generate_outline_dialogue,
    generate_outline_dialogue_stream,
    compile_outline_from_chat,
    get_outline_content,
    update_outline_content,
    get_outline_versions,
    rollback_outline_version,
    save_chat_message,
    get_chat_messages,
    get_chat_messages_raw,
    clear_chat_messages,
    delete_chat_message
)
from ..utils.response import success, error, not_found, bad_request
from ..utils.logger import get_logger
from datetime import datetime
import json

logger = get_logger(__name__)

def json_dumps(obj):
    """SSE安全的JSON序列化（避免转义中文）"""
    return json.dumps(obj, ensure_ascii=False)

outlines_bp = Blueprint('outlines', __name__)


@outlines_bp.route('/api/novels/<int:novel_id>/outline/generate', methods=['POST'])
def generate_outline(novel_id):
    """开启AI对话生成大纲"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return bad_request('消息不能为空')
        
        logger.info(f'开始生成大纲对话: novel_id={novel_id}')
        
        # 从DB获取对话历史
        history = get_chat_messages_raw(novel_id)
        
        # 调用AI生成大纲
        ai_response = generate_outline_dialogue(novel, message, history)
        
        # 保存对话历史到数据库
        save_chat_message(novel_id, 'user', message)
        save_chat_message(novel_id, 'assistant', ai_response)
        
        logger.info(f'大纲对话生成成功: novel_id={novel_id}')
        return success({
            'response': ai_response,
            'session_id': novel_id
        })
    except Exception as e:
        logger.error(f'生成大纲对话失败: {e}')
        return error('生成大纲对话失败')


@outlines_bp.route('/api/novels/<int:novel_id>/outline/chat/stream', methods=['POST'])
def chat_outline_stream(novel_id):
    """大纲对话迭代（流式SSE）"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        data = request.get_json(force=True, silent=True)
        if not data:
            raw = request.get_data(as_text=True)[:200]
            logger.warning(f'大纲对话流式: 无法解析JSON, raw_body={raw}')
            return bad_request('请求体不能为空或不是有效JSON')
        
        message = (data.get('message') or '').strip()
        if not message:
            return bad_request('消息不能为空')
        
        # 从DB获取对话历史
        history = get_chat_messages_raw(novel_id)
        
        logger.info(f'大纲对话流式: novel_id={novel_id}, history_count={len(history)}')
        
        def generate():
            full_response = ""
            try:
                # 先发送用户消息确认
                yield f"data: {json_dumps({'type': 'user_sent', 'content': message})}\n\n"
                
                # 流式生成AI回复
                for chunk in generate_outline_dialogue_stream(novel, message, history):
                    full_response += chunk
                    # SSE格式：data: <json>\n\n
                    yield f"data: {json_dumps({'type': 'chunk', 'content': chunk})}\n\n"
                
                # 完成后保存对话到DB
                save_chat_message(novel_id, 'user', message)
                save_chat_message(novel_id, 'assistant', full_response)
                
                yield f"data: {json_dumps({'type': 'done'})}\n\n"
                
            except Exception as e:
                logger.error(f'流式对话失败: {e}')
                yield f"data: {json_dumps({'type': 'error', 'content': str(e)})}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
    except Exception as e:
        logger.error(f'大纲对话流式请求异常: {e}', exc_info=True)
        return error(f'大纲对话请求失败: {str(e)}')


@outlines_bp.route('/api/novels/<int:novel_id>/outline/accept', methods=['POST'])
def accept_outline(novel_id):
    """采纳对话结果，编译整轮对话为大纲"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        # 检查是否有对话历史
        history = get_chat_messages(novel_id)
        if not history:
            return bad_request('没有对话历史，无法编译大纲')
        
        logger.info(f'开始编译大纲: novel_id={novel_id}, 对话条数={len(history)}')
        
        # 编译整轮对话为大纲
        result = compile_outline_from_chat(novel)
        
        # 清空对话历史
        clear_chat_messages(novel_id)
        
        logger.info(f'大纲编译成功: novel_id={novel_id}, version={result["version"]}')
        return success(data={
            'outline': result['outline'],
            'version': result['version']
        }, message='大纲编译成功')
    except Exception as e:
        logger.error(f'编译大纲失败: {e}')
        return error('编译大纲失败')


@outlines_bp.route('/api/novels/<int:novel_id>/outline', methods=['GET'])
def get_outline(novel_id):
    """获取大纲"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        outline = Outline.query.filter_by(novel_id=novel_id).first()
        if not outline:
            logger.info(f'大纲尚未创建: novel_id={novel_id}')
            return success(None, '大纲尚未创建')
        
        logger.info(f'获取大纲: novel_id={novel_id}, version={outline.version}')
        return success({
            'id': outline.id,
            'content': outline.content,
            'version': outline.version
        })
    except Exception as e:
        logger.error(f'获取大纲失败: {e}')
        return error('获取大纲失败')


@outlines_bp.route('/api/novels/<int:novel_id>/outline', methods=['PUT'])
def update_outline(novel_id):
    """更新大纲（手动编辑）"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        data = request.get_json()
        content = data.get('content', '')
        
        logger.info(f'更新大纲: novel_id={novel_id}')
        update_outline_content(novel, content)
        
        logger.info(f'大纲更新成功: novel_id={novel_id}')
        return success(message='大纲更新成功')
    except Exception as e:
        logger.error(f'更新大纲失败: {e}')
        return error('更新大纲失败')


@outlines_bp.route('/api/novels/<int:novel_id>/outline/versions', methods=['GET'])
def list_outline_versions(novel_id):
    """获取大纲版本列表"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        versions = get_outline_versions(novel)
        
        logger.info(f'获取大纲版本列表: novel_id={novel_id}, count={len(versions)}')
        return success(versions)
    except Exception as e:
        logger.error(f'获取大纲版本列表失败: {e}')
        return error('获取大纲版本列表失败')


@outlines_bp.route('/api/novels/<int:novel_id>/outline/rollback', methods=['POST'])
def rollback_outline(novel_id):
    """回滚到指定版本"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        data = request.get_json()
        version = data.get('version')
        
        if not version:
            return bad_request('版本号不能为空')
        
        logger.info(f'回滚大纲: novel_id={novel_id}, version={version}')
        rollback_outline_version(novel, version)
        
        logger.info(f'大纲回滚成功: novel_id={novel_id}, version={version}')
        return success(message=f'已回滚到版本 {version}')
    except Exception as e:
        logger.error(f'回滚大纲失败: {e}')
        return error('回滚大纲失败')


@outlines_bp.route('/api/novels/<int:novel_id>/outline/chat-history', methods=['GET'])
def get_outline_chat_history(novel_id):
    """获取对话历史"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        history = get_chat_messages(novel_id)
        
        logger.info(f'获取对话历史: novel_id={novel_id}, count={len(history)}')
        return success(history)
    except Exception as e:
        logger.error(f'获取对话历史失败: {e}')
        return error('获取对话历史失败')


@outlines_bp.route('/api/novels/<int:novel_id>/outline/chat-history', methods=['DELETE'])
def clear_outline_chat_history(novel_id):
    """清空对话历史"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        clear_chat_messages(novel_id)
        
        logger.info(f'清空对话历史成功: novel_id={novel_id}')
        return success(message='对话历史已清空')
    except Exception as e:
        logger.error(f'清空对话历史失败: {e}')
        return error('清空对话历史失败')


@outlines_bp.route('/api/novels/<int:novel_id>/outline/chat-message/<int:msg_id>', methods=['DELETE'])
def delete_outline_chat_message(novel_id, msg_id):
    """删除单条对话消息"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        deleted = delete_chat_message(msg_id)
        if not deleted:
            return not_found('消息不存在')
        
        logger.info(f'删除对话消息成功: msg_id={msg_id}')
        return success(message='消息已删除')
    except Exception as e:
        logger.error(f'删除对话消息失败: {e}')
        return error('删除对话消息失败')
