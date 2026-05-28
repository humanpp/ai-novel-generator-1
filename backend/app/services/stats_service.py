# v5/backend/app/services/stats_service.py
# 写作统计服务

from flask import current_app
from ..models.models import db, Novel, Chapter, WritingStats
from datetime import datetime


def calculate_stats(novel):
    """计算写作统计"""
    try:
        # 获取或创建统计记录
        stats = WritingStats.query.filter_by(novel_id=novel.id).first()
        if not stats:
            stats = WritingStats(novel_id=novel.id)
            db.session.add(stats)
        
        # 计算总字数和已完成字数
        chapters = Chapter.query.filter_by(novel_id=novel.id).all()
        
        total_words = 0
        completed_words = 0
        completed_chapters = 0
        
        for chapter in chapters:
            if chapter.word_count:
                total_words += chapter.word_count
                completed_words += chapter.word_count
                completed_chapters += 1
        
        # 更新统计
        stats.total_words = total_words
        stats.completed_words = completed_words
        
        # 计算完成率
        if total_words > 0:
            stats.completion_rate = round(completed_words / total_words * 100, 2)
        
        db.session.commit()
        
        return {
            'total_words': stats.total_words,
            'completed_words': stats.completed_words,
            'completion_rate': stats.completion_rate,
            'writing_duration': stats.writing_duration,
            'last_writing_time': stats.last_writing_time.isoformat() if stats.last_writing_time else None,
            'completed_chapters': completed_chapters,
            'total_chapters': len(chapters)
        }
    except Exception as e:
        db.session.rollback()
        raise


def track_writing_time(novel, session_id, start_time, end_time):
    """记录写作时长"""
    try:
        # 获取或创建统计记录
        stats = WritingStats.query.filter_by(novel_id=novel.id).first()
        if not stats:
            stats = WritingStats(novel_id=novel.id)
            db.session.add(stats)
        
        # 计算时长（秒）
        duration = int((end_time - start_time).total_seconds())
        
        # 累加时长
        stats.writing_duration += duration
        stats.last_writing_time = end_time
        
        db.session.commit()
        
        return {
            'duration': duration,
            'total_duration': stats.writing_duration
        }
    except Exception as e:
        db.session.rollback()
        raise