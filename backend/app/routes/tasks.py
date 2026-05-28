# v5/backend/app/routes/tasks.py
# 异步任务查询API

from flask import Blueprint, request, current_app
import threading
import uuid
from datetime import datetime
from ..utils.response import success, error, not_found
from ..utils.logger import get_logger

logger = get_logger(__name__)

tasks_bp = Blueprint('tasks', __name__)

# 任务存储（内存实现，后续可持久化）
tasks = {}


class AsyncTask:
    """异步任务类"""
    
    def __init__(self, task_id, task_type, novel_id):
        self.task_id = task_id
        self.task_type = task_type
        self.novel_id = novel_id
        self.status = 'pending'  # pending/running/done/failed
        self.progress = 0
        self.result = None
        self.error = None
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
    
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'novel_id': self.novel_id,
            'status': self.status,
            'progress': self.progress,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


def create_task(task_type, novel_id, func, *args, **kwargs):
    """创建异步任务"""
    task_id = str(uuid.uuid4())
    task = AsyncTask(task_id, task_type, novel_id)
    tasks[task_id] = task
    
    # 获取当前应用实例
    app = current_app._get_current_object()
    
    def run_task():
        # 在新线程中创建应用上下文
        with app.app_context():
            try:
                task.status = 'running'
                task.started_at = datetime.utcnow()
                logger.info(f'任务开始执行: task_id={task_id}, type={task_type}')
                
                # 执行任务
                result = func(*args, **kwargs)
                
                task.status = 'done'
                task.result = result
                task.progress = 100
                logger.info(f'任务执行成功: task_id={task_id}, type={task_type}')
            except Exception as e:
                task.status = 'failed'
                task.error = str(e)
                logger.error(f'任务执行失败: task_id={task_id}, type={task_type}, error={e}')
            finally:
                task.completed_at = datetime.utcnow()
    
    # 在新线程中运行
    thread = threading.Thread(target=run_task)
    thread.daemon = True
    thread.start()
    
    logger.info(f'异步任务已创建: task_id={task_id}, type={task_type}, novel_id={novel_id}')
    return task_id


@tasks_bp.route('/api/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """查询异步任务状态"""
    try:
        task = tasks.get(task_id)
        if not task:
            return not_found('任务不存在')
        
        return success(task.to_dict())
    except Exception as e:
        logger.error(f'查询任务状态失败: {e}')
        return error('查询任务状态失败')


@tasks_bp.route('/api/tasks/<task_id>', methods=['DELETE'])
def cancel_task(task_id):
    """取消或清理任务"""
    try:
        task = tasks.get(task_id)
        if not task:
            return not_found('任务不存在')
        
        # 只能取消pending或running状态的任务
        if task.status in ['pending', 'running']:
            task.status = 'cancelled'
            task.completed_at = datetime.utcnow()
            logger.info(f'任务已取消: task_id={task_id}')
            return success(message='任务已取消')
        else:
            # 删除已完成的任务记录
            del tasks[task_id]
            logger.info(f'任务记录已清理: task_id={task_id}')
            return success(message='任务记录已清理')
    except Exception as e:
        logger.error(f'取消/清理任务失败: {e}')
        return error('操作失败')
