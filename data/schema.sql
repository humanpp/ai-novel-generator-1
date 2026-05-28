-- v5/backend/data/schema.sql
-- AI网文小说生成软件 数据库初始化脚本（SQLite）
-- 基于 models.py 生成

-- 小说项目表
CREATE TABLE IF NOT EXISTS novels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    genre VARCHAR(100),
    format VARCHAR(10) NOT NULL DEFAULT 'long',
    workflow_mode VARCHAR(20) NOT NULL,
    summary TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 大纲表（与小说一对一）
CREATE TABLE IF NOT EXISTS outlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    novel_id INTEGER NOT NULL UNIQUE,
    content TEXT,
    version INTEGER DEFAULT 1,
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
);

-- 大纲版本表
CREATE TABLE IF NOT EXISTS outline_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    outline_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (outline_id) REFERENCES outlines(id) ON DELETE CASCADE
);

-- 章节细纲表（流程A）
CREATE TABLE IF NOT EXISTS chapter_outlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    novel_id INTEGER NOT NULL,
    chapter_no INTEGER NOT NULL,
    word_count INTEGER,
    content TEXT,
    events TEXT,
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
);

-- 事件细纲表（流程B）
CREATE TABLE IF NOT EXISTS event_outlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    novel_id INTEGER NOT NULL,
    event_no INTEGER NOT NULL,
    title VARCHAR(200),
    description TEXT,
    cause TEXT,
    effect TEXT,
    related_characters TEXT,
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
);

-- 章节正文表
CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    novel_id INTEGER NOT NULL,
    chapter_no INTEGER NOT NULL,
    title VARCHAR(200),
    content TEXT,
    word_count INTEGER DEFAULT 0,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    chapter_outline_id INTEGER,
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE,
    FOREIGN KEY (chapter_outline_id) REFERENCES chapter_outlines(id) ON DELETE SET NULL
);

-- 章节事件关联表（流程B多事件 → 章节映射）
CREATE TABLE IF NOT EXISTS chapter_event_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES event_outlines(id) ON DELETE CASCADE
);

-- 角色表
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    novel_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(10),
    personality TEXT,
    background TEXT,
    goal TEXT,
    relations TEXT,
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
);

-- 章节角色关联表
CREATE TABLE IF NOT EXISTS chapter_characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    role_desc TEXT,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 角色逻辑链表
CREATE TABLE IF NOT EXISTS character_logic_chains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    novel_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    chapter_no INTEGER,
    motivation TEXT,
    change TEXT,
    content TEXT,
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- 章节版本表
CREATE TABLE IF NOT EXISTS chapter_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    content TEXT,
    word_count INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
);

-- 写作统计表（与小说一对一）
CREATE TABLE IF NOT EXISTS writing_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    novel_id INTEGER NOT NULL UNIQUE,
    total_words INTEGER DEFAULT 0,
    completed_words INTEGER DEFAULT 0,
    completion_rate REAL DEFAULT 0.0,
    writing_duration INTEGER DEFAULT 0,
    last_writing_time DATETIME,
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
);

-- 导入记录表
CREATE TABLE IF NOT EXISTS import_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    novel_id INTEGER NOT NULL,
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    import_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
);

-- 模型配置表
CREATE TABLE IF NOT EXISTS model_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    base_url VARCHAR(255),
    api_key VARCHAR(255),
    model_name VARCHAR(100),
    temperature REAL DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 2048,
    is_default BOOLEAN DEFAULT 0,
    is_builtin BOOLEAN DEFAULT 0
);