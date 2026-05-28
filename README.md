# AI小说创作助手 v5

> ⚠️ **项目状态：几近完善**
>
> 本项目已进入成熟稳定阶段，核心功能全部实现并经过充分测试。代码结构完整、文档齐全，可直接用于生产环境。
>
> **主要特点：**
> - ✅ 全流程 AI 写作功能已完成
> - ✅ 双工作流模式（章节流+事件流）已实现
> - ✅ 15 张数据表设计完整
> - ✅ 前后端分离架构稳定
> - ✅ 安全特性（API Key 加密、XSS 防护）已实现
> - ✅ 多 LLM 提供商支持
>
> **适用场景：**
> - 个人网文创作
> - AI 写作工具开发参考
> - 全栈项目学习
>
> **维护状态：** 积极维护中，欢迎 Issue 和 PR。

---

基于大语言模型（LLM）的AI辅助网文小说创作平台，支持从大纲规划、章节撰写、角色管理到统计分析的全流程AI写作。

## 功能特性

### 核心功能

- **项目管理**：创建、编辑、删除小说项目，支持长篇/短篇模式和章节/事件两种工作流
- **大纲规划**：通过 AI 对话式交互生成和迭代小说大纲，支持多版本管理
- **章节撰写**：AI 自动生成章节正文内容，支持逐章生成和续写，内置 Markdown 编辑器
- **章节细纲**（流程A）：先生成章节细纲再撰文，确保情节逻辑严谨
- **事件大纲**（流程B）：以事件为核心驱动章节生成，自动映射事件到章节
- **角色管理**：AI 自动抽取角色、手动创建/编辑角色、角色反推，支持字段丰富的角色档案（性格、背景、目标动机）
- **关系脑图**：基于 ECharts 可视化展示角色关系网络，支持力导向图和章节-事件双栏映射图
- **导入导出**：支持导入已有小说文本和导出完整小说项目
- **写作统计**：实时统计总字数、完成章节数、完成度百分比、写作时长等

### 技术亮点

- 支持多种 LLM 提供商：**OpenAI**、**LMStudio**、**Ollama**、**vLLM** 及任何 OpenAI 兼容 API
- API Key 加密存储（Fernet 对称加密）
- 异步任务机制：耗时 AI 操作通过任务轮询实现，不阻塞前端
- 纯前端无框架架构：原生 JavaScript + Bootstrap 5 组件化设计
- 自定义 Markdown 渲染器：集成代码高亮、安全消毒、复制按钮

## 项目结构

```
v5/
├── backend/                     # 后端 Flask 应用
│   ├── run.py                   # 应用启动入口
│   └── app/
│       ├── __init__.py          # Flask 工厂函数、蓝图注册、错误处理
│       ├── config.py            # 配置管理（开发/生产/测试环境）
│       ├── prompts.py           # AI 提示词模板
│       ├── models/
│       │   ├── __init__.py
│       │   └── models.py        # 数据模型（15张表）
│       ├── routes/
│       │   ├── __init__.py      # 蓝图注册
│       │   ├── novels.py        # 小说项目 CRUD
│       │   ├── outlines.py      # 大纲 AI 对话
│       │   ├── chapter_outlines.py  # 章节细纲（流程A）
│       │   ├── event_outlines.py    # 事件大纲（流程B）
│       │   ├── chapters.py      # 章节生成与管理
│       │   ├── characters.py    # 角色管理
│       │   ├── character_logic.py   # 角色逻辑链
│       │   ├── mindmap.py       # 角色关系脑图
│       │   ├── imports.py       # 小说导入
│       │   ├── exports.py       # 小说导出
│       │   ├── stats.py         # 写作统计
│       │   ├── tasks.py         # 异步任务管理
│       │   └── models_config.py # LLM 模型配置
│       ├── services/
│       │   ├── __init__.py
│       │   ├── model_service.py     # 模型配置业务逻辑
│       │   ├── outline_service.py   # 大纲生成服务
│       │   ├── chapter_service.py   # 章节/细纲生成服务
│       │   ├── character_service.py # 角色抽取服务
│       │   ├── export_service.py    # 导出服务
│       │   ├── import_service.py    # 导入服务
│       │   └── stats_service.py     # 统计服务
│       ├── llm/
│       │   ├── __init__.py
│       │   └── client.py        # LLM 通用客户端（支持流式/非流式）
│       └── utils/
│           ├── __init__.py
│           ├── encryption.py    # API Key 加密/解密
│           ├── response.py      # 统一 API 响应格式
│           ├── logger.py        # 日志配置
│           ├── file_utils.py    # 文件处理工具
│           └── json_parser.py   # JSON 解析修复
├── frontend/                    # 前端纯静态页面
│   ├── index.html               # 主页面（SPA 单页应用）
│   ├── css/
│   │   └── style.css            # 全局样式
│   └── js/
│       ├── api.js               # API 请求封装层
│       ├── app.js               # 主应用控制器
│       ├── components/
│       │   ├── projectManager.js    # 项目管理组件
│       │   ├── outlineChat.js       # 大纲 AI 对话组件
│       │   ├── eventChain.js        # 事件链/章节管理组件
│       │   ├── characterManager.js  # 角色管理组件
│       │   ├── modelManager.js      # 模型配置组件
│       │   ├── mindmapView.js       # 章节-事件脑图组件
│       │   └── statsBar.js          # 底部统计栏组件
│       └── utils/
│           ├── stateManager.js      # 全局状态管理
│           ├── helpers.js           # 通用辅助函数
│           └── markdownRenderer.js  # Markdown 渲染模块
├── data/
│   ├── schema.sql               # 数据库建表 SQL
│   └── novel.db                 # SQLite 数据库文件
├── requirements.txt             # Python 依赖
└── README.md
```

## 快速开始

### 环境要求

- Python 3.12+
- 一个可用的 LLM 服务（任选其一）：
  - [OpenAI API](https://platform.openai.com/)（云端）
  - [LMStudio](https://lmstudio.ai/)（本地，默认端口 1234）
  - [Ollama](https://ollama.com/)（本地，默认端口 11434）
  - [vLLM](https://github.com/vllm-project/vllm)（本地/服务器，默认端口 8000）
  - 或任何 OpenAI 兼容的 API 服务

### 安装步骤

1. **克隆或解压项目**

```bash
cd v5
```

1. **创建虚拟环境（推荐）**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

1. **安装 Python 依赖**

```bash
pip install -r requirements.txt
```

1. **启动后端服务**

```bash
cd backend
python run.py
```

服务启动后，访问 <http://localhost:5000> 即可使用。

### 配置 LLM 模型

首次使用需要在界面中配置 LLM 模型：

1. 点击顶部导航栏的 **模型：未配置** 按钮
2. 点击 **添加模型**，选择提供商（或手动配置）
3. 填写 Base URL 和模型名称，点击 **测试连接** 验证
4. 点击 **添加模型** 保存配置
5. 点击 **设为默认** 激活该模型

支持的提供商预设：

| 提供商      | 默认地址                        | 用途          |
| -------- | --------------------------- | ----------- |
| LMStudio | `http://localhost:1234/v1`  | 本地开源模型      |
| Ollama   | `http://localhost:11434/v1` | 本地开源模型      |
| vLLM     | `http://localhost:8000/v1`  | 本地/服务器高性能推理 |
| OpenAI   | `https://api.openai.com/v1` | 云端 GPT 系列   |

## 工作流程

### 模式一：章节工作流（传统流程A）

```
创建项目 → 对话生成总大纲 → 生成章节细纲 → AI逐章撰写正文
```

1. 创建小说项目，选择 **章节** 模式
2. 在对话区与 AI 交互，生成和完善总大纲
3. 点击 **批量生成章节细纲**，AI 为每章生成详细情节规划
4. 逐章点击 **生成/续写**，AI 根据细纲撰写正文
5. 单章支持与 AI 对话式精修

### 模式二：事件工作流（流程B）

```
创建项目 → 创建事件大纲 → 创建章节 → 事件映射章节 → AI逐章撰写
```

1. 创建小说项目，选择 **事件** 模式
2. 在事件区添加/生成关键事件（起因、经过、结果）
3. 创建章节占位
4. 使用 **脑图** 将事件拖拽映射到对应章节
5. AI 根据关联的事件内容逐章撰写正文

## API 接口概览

所有 API 返回统一 JSON 格式：

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

### 项目管理

| 方法     | 路径                | 说明       |
| ------ | ----------------- | -------- |
| GET    | `/api/novels`     | 获取所有项目列表 |
| POST   | `/api/novels`     | 创建新项目    |
| GET    | `/api/novels/:id` | 获取项目详情   |
| PUT    | `/api/novels/:id` | 更新项目信息   |
| DELETE | `/api/novels/:id` | 删除项目     |

### 大纲对话

| 方法   | 路径                                  | 说明       |
| ---- | ----------------------------------- | -------- |
| GET  | `/api/novels/:id/outlines`          | 获取当前大纲   |
| POST | `/api/novels/:id/outlines/chat`     | 发送大纲对话消息 |
| GET  | `/api/novels/:id/outlines/versions` | 获取大纲版本历史 |
| POST | `/api/novels/:id/outlines/rollback` | 回滚到指定版本  |

### 章节管理

| 方法     | 路径                                         | 说明      |
| ------ | ------------------------------------------ | ------- |
| GET    | `/api/novels/:id/chapters`                 | 获取章节列表  |
| POST   | `/api/novels/:id/chapters`                 | 创建章节    |
| GET    | `/api/novels/:id/chapters/:ch_no`          | 获取章节内容  |
| PUT    | `/api/novels/:id/chapters/:ch_no`          | 更新章节    |
| DELETE | `/api/novels/:id/chapters/:ch_no`          | 删除章节    |
| POST   | `/api/novels/:id/chapters/:ch_no/generate` | AI 生成章节 |
| POST   | `/api/novels/:id/chapters/:ch_no/continue` | AI 续写章节 |
| POST   | `/api/novels/:id/chapters/:ch_no/chat`     | 章节对话精修  |

### 章节细纲（流程A）

| 方法   | 路径                                                   | 说明     |
| ---- | ---------------------------------------------------- | ------ |
| POST | `/api/novels/:id/chapter-outlines/generate`          | 批量生成细纲 |
| POST | `/api/novels/:id/chapter-outlines/:ch_no/generate`   | 生成单章细纲 |
| GET  | `/api/novels/:id/chapter-outlines`                   | 获取细纲列表 |
| PUT  | `/api/novels/:id/chapter-outlines/:ch_no`            | 更新细纲   |
| POST | `/api/novels/:id/chapter-outlines/:ch_no/regenerate` | 重新生成   |

### 事件大纲（流程B）

| 方法     | 路径                                 | 说明      |
| ------ | ---------------------------------- | ------- |
| GET    | `/api/novels/:id/events`           | 获取事件列表  |
| POST   | `/api/novels/:id/events`           | 创建事件    |
| PUT    | `/api/novels/:id/events/:event_id` | 更新事件    |
| DELETE | `/api/novels/:id/events/:event_id` | 删除事件    |
| POST   | `/api/novels/:id/events/generate`  | AI 生成事件 |

### 角色管理

| 方法     | 路径                                    | 说明       |
| ------ | ------------------------------------- | -------- |
| GET    | `/api/novels/:id/characters`          | 获取角色列表   |
| POST   | `/api/novels/:id/characters`          | 创建角色     |
| GET    | `/api/novels/:id/characters/:char_id` | 获取角色详情   |
| PUT    | `/api/novels/:id/characters/:char_id` | 更新角色     |
| DELETE | `/api/novels/:id/characters/:char_id` | 删除角色     |
| POST   | `/api/novels/:id/characters/extract`  | AI 抽取角色  |
| GET    | `/api/novels/:id/characters/mindmap`  | 获取角色脑图数据 |

### 模型配置

| 方法     | 路径                       | 说明     |
| ------ | ------------------------ | ------ |
| GET    | `/api/models`            | 获取模型列表 |
| POST   | `/api/models`            | 添加模型配置 |
| PUT    | `/api/models/:id`        | 更新模型配置 |
| DELETE | `/api/models/:id`        | 删除模型配置 |
| POST   | `/api/models/:id/switch` | 切换默认模型 |
| POST   | `/api/models/test`       | 测试模型连接 |

## 数据库设计

使用 SQLite 数据库，主要数据表：

| 表名                       | 说明        |
| ------------------------ | --------- |
| `novels`                 | 小说项目      |
| `outlines`               | 当前大纲      |
| `outline_versions`       | 大纲版本历史    |
| `chat_messages`          | AI 对话消息记录 |
| `chapter_outlines`       | 章节细纲      |
| `event_outlines`         | 事件大纲      |
| `chapters`               | 章节正文      |
| `chapter_versions`       | 章节版本历史    |
| `characters`             | 角色信息      |
| `chapter_characters`     | 角色-章节关联   |
| `character_logic_chains` | 角色逻辑链     |
| `chapter_event_mapping`  | 章节-事件映射   |
| `writing_stats`          | 写作统计      |
| `model_configs`          | LLM 模型配置  |
| `import_records`         | 导入记录      |

## 技术栈

### 后端

- **Flask** — Web 框架
- **Flask-CORS** — 跨域支持
- **Flask-SQLAlchemy** — ORM（SQLite）
- **OpenAI Python SDK** — LLM API 调用
- **cryptography (Fernet)** — API Key 加密存储

### 前端

- **原生 JavaScript** — 零框架、组件化 SPA
- **Bootstrap 5** — UI 框架
- **Bootstrap Icons** — 图标库
- **ECharts** — 脑图/关系图可视化
- **marked** — Markdown 解析
- **highlight.js** — 代码高亮
- **DOMPurify** — HTML 安全消毒

## 配置说明

环境配置通过 `backend/app/config.py` 管理，支持三种环境：

- **development**（默认）：DEBUG 开启，使用 `data/novel.db`
- **production**：需要设置 `SECRET_KEY` 环境变量
- **testing**：使用内存数据库

修改启动环境：

```python
# backend/run.py
app = create_app('development')  # 改为 'production' 或 'testing'
```

## 安全特性

- API Key 使用 Fernet 对称加密存储，基于 `SECRET_KEY` 派生密钥
- 前端 Markdown 渲染通过 DOMPurify 进行 XSS 防护
- 密码字段前端掩码显示（`****`），不返回明文
- 统一错误处理，避免敏感信息泄露

## License

MIT
