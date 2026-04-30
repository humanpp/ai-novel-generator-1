# AI网文小说生成软件 v5

一个面向网文作者的AI辅助创作工具，支持长篇小说与短篇小说的全流程创作。

## 🙏 致谢

特别感谢 **Xiaomi Mimo** 慷慨提供的 [**2 亿 Token** ](https://100t.xiaomimimo.com/)额度支持（1天已经干完了）。  
没有这笔“巨款”，代码根本跑不起来。衷心感谢！
![Demo演示3](https://github.com/humanpp/ai-novel-generator-demo/blob/main/assets/Snipaste_2026-04-30_19-31-56.png)
---

## ⚠️ 已知不足（因为 Token 用完了）

Token 额度耗尽，下列问题只能遗憾留待未来慢慢修补：

- **Prompt 尚未优化至最佳**  
  提示词远没调到最优状态，响应质量仍有明显提升空间。
- **事件链工作流未完成**  
  核心的事件链（Event Chain）工作流还停在想法阶段，我架构书写的好好地，AI不按我规划的工作。
- **Bug 还有不少**  
  已知和未知的 bug 数量感人，稳定性全靠运气。
- **脑图不支持修改**  
  脑图视图目前是“只读”状态，无法直接编辑节点，必须绕道操作。

> 🕊️ 等下一次“Token 自由”的时候，再回来填这些坑。

---
![Demo演示1](https://github.com/humanpp/ai-novel-generator-demo/blob/main/assets/Snipaste_2026-04-30_19-09-53.png)
![Demo演示2](https://github.com/humanpp/ai-novel-generator-demo/blob/main/assets/Snipaste_2026-04-30_19-11-15.png)
---

## 功能特性

- **双工作流模式**
  - 流程A：线性章节细纲模式（大纲 → 章节细纲 → 角色逻辑链 → 章节正文）
  - 流程B：事件驱动模式（大纲 → 事件链 → 角色逻辑链 → 章节正文）

- **核心功能**
  - 对话式大纲生成
  - 章节细纲/事件链生成
  - 角色管理与关系脑图
  - 章节正文生成
  - 版本管理与回滚
  - 多格式导出（Word/TXT/EPUB）
  - 写作统计
  - 模型管理（支持OpenAI兼容接口）

## 技术栈

### 后端

- Python 3.12
- Flask 3.0
- Flask-SQLAlchemy
- SQLite
- python-docx
- ebooklib
- openai

### 前端

- HTML5 + CSS3
- JavaScript (ES6+)
- Bootstrap 5
- Axios
- ECharts

## 快速开始

### 1. 安装后端依赖

```bash
cd v5
pip install -r requirements.txt
```

### 2. 启动后端服务

```bash
cd backend
python run.py
```

后端服务将在 http://localhost:5000 启动

### 3. 访问前端

在浏览器中打开 `http://localhost:5000` 。

## 目录结构

```
v5/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── __init__.py        # Flask应用工厂
│   │   ├── config.py          # 配置文件
│   │   ├── llm/               # LLM客户端
│   │   │   ├── __init__.py
│   │   │   └── client.py
│   │   ├── models/            # 数据模型
│   │   │   ├── __init__.py
│   │   │   └── models.py
│   │   ├── routes/            # API路由
│   │   │   ├── __init__.py
│   │   │   ├── novels.py
│   │   │   ├── outlines.py
│   │   │   ├── chapters.py
│   │   │   ├── characters.py
│   │   │   └── ...
│   │   ├── services/          # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── outline_service.py
│   │   │   ├── chapter_service.py
│   │   │   ├── character_service.py
│   │   │   └── ...
│   │   └── utils/             # 工具函数
│   │       ├── __init__.py
│   │       ├── encryption.py
│   │       └── file_utils.py
│   ├── tests/                 # 测试文件
│   └── run.py                 # 启动脚本
├── frontend/                   # 前端代码
│   ├── index.html             # 主页面
│   ├── css/
│   │   └── style.css          # 样式文件
│   ├── js/
│   │   ├── api.js             # API封装
│   │   ├── app.js             # 主入口
│   │   ├── components/        # 组件
│   │   │   ├── projectManager.js
│   │   │   └── statsBar.js
│   │   └── utils/
│   │       └── stateManager.js
│   └── assets/
│       └── images/
├── data/                       # 数据库文件
│   └── schema.sql
├── uploads/                    # 上传文件目录
├── exports/                    # 导出文件目录
├── requirements.txt            # Python依赖
└── README.md                   # 本文件
```

## API文档

### 项目管理

- `GET /api/novels` - 获取项目列表
- `POST /api/novels` - 创建新项目
- `GET /api/novels/:id` - 获取项目详情
- `PUT /api/novels/:id` - 更新项目
- `DELETE /api/novels/:id` - 删除项目

### 大纲管理

- `POST /api/novels/:id/outline/generate` - 生成大纲
- `POST /api/novels/:id/outline/chat` - 大纲对话
- `POST /api/novels/:id/outline/accept` - 采纳大纲
- `GET /api/novels/:id/outline` - 获取大纲
- `PUT /api/novels/:id/outline` - 更新大纲
- `GET /api/novels/:id/outline/versions` - 获取版本列表
- `POST /api/novels/:id/outline/rollback` - 回滚版本

### 章节细纲（流程A）

- `POST /api/novels/:id/chapter-outlines/generate` - 生成章节细纲
- `GET /api/novels/:id/chapter-outlines` - 获取章节细纲列表
- `GET /api/novels/:id/chapter-outlines/:ch_no` - 获取单章细纲
- `PUT /api/novels/:id/chapter-outlines/:ch_no` - 更新章节细纲

### 事件细纲（流程B）

- `POST /api/novels/:id/event-outlines/generate` - 生成事件链
- `GET /api/novels/:id/event-outlines` - 获取事件列表
- `PUT /api/novels/:id/event-outlines/reorder` - 重排事件顺序

### 角色管理

- `POST /api/novels/:id/characters/extract` - AI抽取角色
- `GET /api/novels/:id/characters` - 获取角色列表
- `POST /api/novels/:id/characters` - 创建角色
- `GET /api/novels/:id/characters/mindmap` - 获取脑图数据

### 章节正文

- `POST /api/novels/:id/chapters/:ch_no/generate` - 生成章节
- `POST /api/novels/:id/chapters/generate-batch` - 批量生成
- `GET /api/novels/:id/chapters` - 获取章节列表
- `GET /api/novels/:id/chapters/:ch_no` - 获取章节内容
- `PUT /api/novels/:id/chapters/:ch_no` - 更新章节

### 导入导出

- `POST /api/novels/import` - 导入小说
- `POST /api/novels/:id/export/docx` - 导出Word
- `POST /api/novels/:id/export/txt` - 导出TXT
- `POST /api/novels/:id/export/epub` - 导出EPUB

### 模型管理

- `GET /api/models` - 获取模型列表
- `POST /api/models` - 添加模型
- `POST /api/models/test` - 测试模型
- `POST /api/models/switch` - 切换默认模型

### 写作统计

- `GET /api/novels/:id/stats` - 获取统计
- `POST /api/novels/:id/stats/start-writing` - 开始计时
- `POST /api/novels/:id/stats/stop-writing` - 停止计时

### 异步任务

- `GET /api/tasks/:task_id` - 查询任务状态

## 使用说明

1. **配置模型**：首次使用前，请在"模型设置"中配置LLM模型（支持Ollama、vLLM、LM Studio等OpenAI兼容接口）

2. **创建项目**：点击"创建新项目"，填写项目信息，选择工作流模式

3. **生成大纲**：在大纲对话界面输入你的故事想法，AI会帮你生成大纲

4. **生成细纲/事件链**：
   - 流程A：生成章节细纲
   - 流程B：生成事件链

5. **生成角色**：AI可以从大纲中自动抽取角色

6. **生成正文**：选择章节，点击"AI生成"

7. **导出作品**：支持导出为Word、TXT、EPUB格式

## 注意事项

- 首次运行会自动创建数据库
- 上传文件大小限制为16MB
- API密钥会加密存储
- 建议使用Chrome或Firefox浏览器

## 开发说明

如需修改或扩展功能：

1. 后端API在 `backend/app/routes/` 目录
2. 业务逻辑在 `backend/app/services/` 目录
3. 数据模型在 `backend/app/models/models.py`
4. 前端组件在 `frontend/js/components/` 目录

## 许可证

MIT License
