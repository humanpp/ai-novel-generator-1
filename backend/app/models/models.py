# v5/backend/app/models/models.py

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Text, Float, Boolean, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

db = SQLAlchemy()

class Novel(db.Model):
    __tablename__ = 'novels'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(100))
    format = db.Column(db.String(10), nullable=False, default='long')  # long / short
    workflow_mode = db.Column(db.String(20), nullable=False)  # chapter / event
    summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    outline = db.relationship('Outline', backref='novel', uselist=False, cascade='all, delete-orphan')
    chapter_outlines = db.relationship('ChapterOutline', backref='novel', cascade='all, delete-orphan')
    event_outlines = db.relationship('EventOutline', backref='novel', cascade='all, delete-orphan')
    chapters = db.relationship('Chapter', backref='novel', cascade='all, delete-orphan')
    characters = db.relationship('Character', backref='novel', cascade='all, delete-orphan')
    character_logic_chains = db.relationship('CharacterLogicChain', backref='novel', cascade='all, delete-orphan')
    writing_stats = db.relationship('WritingStats', backref='novel', uselist=False, cascade='all, delete-orphan')
    import_records = db.relationship('ImportRecord', backref='novel', cascade='all, delete-orphan')

class Outline(db.Model):
    __tablename__ = 'outlines'

    id = db.Column(db.Integer, primary_key=True)
    novel_id = db.Column(db.Integer, db.ForeignKey('novels.id', ondelete='CASCADE'), nullable=False, unique=True)
    content = db.Column(db.Text)
    version = db.Column(db.Integer, default=1)

    # 关系
    versions = db.relationship('OutlineVersion', backref='outline', cascade='all, delete-orphan')

class OutlineVersion(db.Model):
    __tablename__ = 'outline_versions'

    id = db.Column(db.Integer, primary_key=True)
    outline_id = db.Column(db.Integer, db.ForeignKey('outlines.id', ondelete='CASCADE'), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    """大纲/AI对话消息持久化"""
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    novel_id = db.Column(db.Integer, db.ForeignKey('novels.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # user / assistant / system
    content = db.Column(db.Text, nullable=False)
    context_type = db.Column(db.String(20), default='outline')  # outline / event — 对话场景
    chapter_no = db.Column(db.Integer, nullable=True)  # 事件对话关联的章节号
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    novel = db.relationship('Novel', backref=db.backref('chat_messages', cascade='all, delete-orphan', lazy='dynamic'))

class ChapterOutline(db.Model):
    __tablename__ = 'chapter_outlines'

    id = db.Column(db.Integer, primary_key=True)
    novel_id = db.Column(db.Integer, db.ForeignKey('novels.id', ondelete='CASCADE'), nullable=False)
    chapter_no = db.Column(db.Integer, nullable=False)
    word_count = db.Column(db.Integer)
    content = db.Column(db.Text)
    events = db.Column(db.Text)  # JSON string

    # 关系
    chapters = db.relationship('Chapter', backref='chapter_outline', lazy='dynamic')

class EventOutline(db.Model):
    __tablename__ = 'event_outlines'

    id = db.Column(db.Integer, primary_key=True)
    novel_id = db.Column(db.Integer, db.ForeignKey('novels.id', ondelete='CASCADE'), nullable=False)
    event_no = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    cause = db.Column(db.Text)
    effect = db.Column(db.Text)
    related_characters = db.Column(db.Text)  # JSON

    # 关系
    chapter_mappings = db.relationship('ChapterEventMapping', backref='event_outline', cascade='all, delete-orphan')

class Chapter(db.Model):
    __tablename__ = 'chapters'

    id = db.Column(db.Integer, primary_key=True)
    novel_id = db.Column(db.Integer, db.ForeignKey('novels.id', ondelete='CASCADE'), nullable=False)
    chapter_no = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    word_count = db.Column(db.Integer, default=0)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    chapter_outline_id = db.Column(db.Integer, db.ForeignKey('chapter_outlines.id', ondelete='SET NULL'), nullable=True)  # 流程A使用，流程B为NULL

    # 关系
    versions = db.relationship('ChapterVersion', backref='chapter', cascade='all, delete-orphan')
    event_mappings = db.relationship('ChapterEventMapping', backref='chapter', cascade='all, delete-orphan')
    character_associations = db.relationship('ChapterCharacter', backref='chapter', cascade='all, delete-orphan')

class ChapterEventMapping(db.Model):
    __tablename__ = 'chapter_event_mapping'

    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id', ondelete='CASCADE'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event_outlines.id', ondelete='CASCADE'), nullable=False)
    sort_order = db.Column(db.Integer, default=0)

class ChapterCharacter(db.Model):
    __tablename__ = 'chapter_characters'

    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id', ondelete='CASCADE'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('characters.id', ondelete='CASCADE'), nullable=False)
    role_desc = db.Column(db.Text)

class Character(db.Model):
    __tablename__ = 'characters'

    id = db.Column(db.Integer, primary_key=True)
    novel_id = db.Column(db.Integer, db.ForeignKey('novels.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10))
    personality = db.Column(db.Text)
    background = db.Column(db.Text)
    goal = db.Column(db.Text)
    relations = db.Column(db.Text)  # JSON

    # 关系
    logic_chains = db.relationship('CharacterLogicChain', backref='character', cascade='all, delete-orphan')
    chapter_associations = db.relationship('ChapterCharacter', backref='character', cascade='all, delete-orphan')

class CharacterLogicChain(db.Model):
    __tablename__ = 'character_logic_chains'

    id = db.Column(db.Integer, primary_key=True)
    novel_id = db.Column(db.Integer, db.ForeignKey('novels.id', ondelete='CASCADE'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('characters.id', ondelete='CASCADE'), nullable=False)
    chapter_no = db.Column(db.Integer)  # 章节序号或事件序号
    motivation = db.Column(db.Text)
    change = db.Column(db.Text)
    content = db.Column(db.Text)

class ChapterVersion(db.Model):
    __tablename__ = 'chapter_versions'

    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id', ondelete='CASCADE'), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text)
    word_count = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WritingStats(db.Model):
    __tablename__ = 'writing_stats'

    id = db.Column(db.Integer, primary_key=True)
    novel_id = db.Column(db.Integer, db.ForeignKey('novels.id', ondelete='CASCADE'), nullable=False, unique=True)
    total_words = db.Column(db.Integer, default=0)
    completed_words = db.Column(db.Integer, default=0)
    completion_rate = db.Column(db.Float, default=0.0)
    writing_duration = db.Column(db.Integer, default=0)  # 秒
    last_writing_time = db.Column(db.DateTime)

class ImportRecord(db.Model):
    __tablename__ = 'import_records'

    id = db.Column(db.Integer, primary_key=True)
    novel_id = db.Column(db.Integer, db.ForeignKey('novels.id', ondelete='CASCADE'), nullable=False)
    file_name = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    import_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending/processing/done/failed

class ModelConfig(db.Model):
    __tablename__ = 'model_configs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    provider = db.Column(db.String(50), nullable=False)
    base_url = db.Column(db.String(255))
    api_key = db.Column(db.String(255))  # 实际应加密存储，由encryption.py工具函数处理
    model_name = db.Column(db.String(100))
    temperature = db.Column(db.Float, default=0.7)
    max_tokens = db.Column(db.Integer, default=2048)
    is_default = db.Column(db.Boolean, default=False)
    is_builtin = db.Column(db.Boolean, default=False)
    
    def to_dict(self, mask_key=True):
        """将模型配置转换为字典
        
        Args:
            mask_key: 是否对API密钥进行脱敏处理，默认为True
        """
        api_key_value = self.api_key
        if mask_key and api_key_value:
            api_key_value = '****'
        
        return {
            'id': self.id,
            'name': self.name,
            'provider': self.provider,
            'base_url': self.base_url,
            'api_key': api_key_value,
            'model_name': self.model_name,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'is_default': self.is_default,
            'is_builtin': self.is_builtin
        }