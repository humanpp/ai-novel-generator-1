# v5/backend/app/routes/stats.py
# 写作统计API

from flask import Blueprint, request
from ..models.models import db, Novel, WritingStats
from ..services.stats_service import calculate_stats, track_writing_time
from ..utils.response import success, error, not_found, bad_request
from ..utils.logger import get_logger
import uuid
from datetime import datetime

logger = get_logger(__name__)

stats_bp = Blueprint('stats', __name__)

# 写作会话缓存
writing_sessions = {}


@stats_bp.route('/api/novels/<int:novel_id>/stats', methods=['GET'])
def get_stats(novel_id):
    """获取写作统计"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        stats = calculate_stats(novel)
        
        logger.info(f'获取写作统计: novel_id={novel_id}')
        return success(stats)
    except Exception as e:
        logger.error(f'获取写作统计失败: {e}')
        return error('获取写作统计失败')


@stats_bp.route('/api/novels/<int:novel_id>/stats/start-writing', methods=['POST'])
def start_writing(novel_id):
    """开始写作计时"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        session_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        # 保存到缓存
        writing_sessions[session_id] = {
            'novel_id': novel_id,
            'start_time': start_time
        }
        
        logger.info(f'开始写作计时: novel_id={novel_id}, session_id={session_id}')
        return success({
            'session_id': session_id,
            'start_time': start_time.isoformat()
        })
    except Exception as e:
        logger.error(f'开始写作计时失败: {e}')
        return error('开始写作计时失败')


@stats_bp.route('/api/novels/<int:novel_id>/stats/stop-writing', methods=['POST'])
def stop_writing(novel_id):
    """停止计时并累加时长"""
    try:
        novel = Novel.query.get(novel_id)
        if not novel:
            return not_found('项目不存在')
        
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return bad_request('会话ID不能为空')
        
        session = writing_sessions.get(session_id)
        if not session:
            return not_found('会话不存在或已过期')
        
        end_time = datetime.utcnow()
        start_time = session['start_time']
        
        # 计算时长（秒）
        duration = int((end_time - start_time).total_seconds())
        
        # 更新统计
        track_writing_time(novel, session_id, start_time, end_time)
        
        # 删除会话
        del writing_sessions[session_id]
        
        logger.info(f'停止写作计时: novel_id={novel_id}, session_id={session_id}, duration={duration}s')
        return success({
            'duration': duration
        }, f'写作时长已记录: {duration}秒')
    except Exception as e:
        logger.error(f'停止写作计时失败: {e}')
        return error('停止写作计时失败')
