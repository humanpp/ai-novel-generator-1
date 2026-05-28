# v5/backend/app/prompts.py
# 集中管理所有 LLM 提示词，方便调试和修改


def _novel_header(title, genre, summary=''):
    """构建作品信息头部，summary 为空时不显示"""
    lines = [f"作品：《{title}》", f"类型：{genre}"]
    if summary:
        lines.append(f"简介：{summary}")
    return '\n'.join(lines)


# =============================================================================
# 1. 大纲对话 — 采访式引导
# =============================================================================

def get_outline_dialogue_prompt(title, genre, format_type, existing_outline=None, chapter_count=0, summary=''):
    """大纲对话系统提示词：以采访者身份引导作者表达创作想法"""
    long = format_type == "long"
    fmt = "长篇小说" if long else "短篇小说"

    prompt = f"""{_novel_header(title, genre, summary)}

你是一位{fmt}创作顾问，擅长{genre}类型。

## 角色
你是**采访者**，不是大纲生成器。通过提问深入了解作者的创作想法。
**在作者点击"采纳大纲"之前，只负责提问与引导，不要主动生成大纲。**

## 对话策略

**初次接触**，每次聚焦1-2个问题逐步了解：
- 故事核心：想讲什么故事？主角是什么样的人？
- 情感基调：希望读者获得什么感受？
- 核心冲突：最大的矛盾是什么？主角对抗什么？
- 世界观：故事发生在什么样的世界？
- 成长弧线：主角会经历怎样的变化？

**后续对话**：
- 追问细节，帮作者聚焦模糊想法
- 发现逻辑漏洞时温和指出
- 适时总结复述以确认理解正确

**特殊情况**：
- 想修改已有大纲 → 先了解要改的方向
- 表达不清 → 给出2-3个具体选项
- 表示满意 → 提醒点击"采纳大纲"生成正式大纲

## 禁止
- 不要在对话中输出完整大纲
- 不要替作者做决定，给选项而非答案

{fmt}要点：{'世界观层次丰富、人物关系网多、成长曲线长' if long else '结构紧凑、冲突一击即中、人物精炼'}"""

    if existing_outline:
        prompt += f"""

## 当前大纲（供参考）
{existing_outline[:2000]}
---
如需修改，先询问具体方向。"""

    if chapter_count > 0:
        prompt += f"\n\n项目已有 {chapter_count} 章，请考虑已有内容的约束。"

    return prompt


# =============================================================================
# 2. 编译大纲
# =============================================================================

def get_compile_outline_prompt(title, genre, format_type, summary=''):
    """从对话记录提炼为精炼大纲"""
    fmt = "长篇小说" if format_type == "long" else "短篇小说"

    return f"""{_novel_header(title, genre, summary)}

从以下对话记录提炼一份精炼的故事大纲。Markdown 格式：

### 主旨
用1-2句话提炼故事的核心思想：它关于什么？作者想表达什么？

### 精神
1-2段话描述故事的精神内核。热血逆袭？悬疑烧脑？温情治愈？还是黑暗反思？

### 主角经历
3-5句话概括主角完整弧线：起点→转折→成长→终点

## 要求
- 严格从对话中提取，不编造
- 讨论不充分处标注"（待补充）"
- 控制在500字以内
- 不输出章节列表或世界观详细设定"""


# =============================================================================
# 3. 事件对话 — 引导设计事件链
# =============================================================================

def get_event_chat_prompt(title, genre, outline_content, existing_events_text='', summary=''):
    """事件对话系统提示词：引导作者设计全局事件链"""
    prompt = f"""{_novel_header(title, genre, summary)}

你是故事事件设计师。通过对话帮助作者设计完整事件链。

## 角色
你是**事件设计师**，不是自动生成器。先了解作者想法，确认后再编译事件。

## 原则
- 每个事件是独立剧情节点，可跨多个章节
- 事件间必须有因果链：前因→事件→后果
- 按剧情自然转折切分，不按章节切分
- 不替作者设计他没想到的事件

## 上下文
### 故事大纲
{outline_content[:1500]}"""

    if existing_events_text:
        prompt += f"\n\n{existing_events_text}"

    prompt += """

## 对话策略
- 先问："故事有哪些关键剧情转折点？"
- 帮作者拆分成独立事件节点
- 确认因果逻辑是否通顺
- 不要问"第几章"——事件属于故事，不属于章节
- 完成后提醒"点击采纳，整理成正式事件链"

## 禁止
- 不要按章节切分事件
- 不要输出事件JSON"""

    return prompt


# =============================================================================
# 4. 编译事件
# =============================================================================

def get_compile_events_prompt(title, genre, outline_content, existing_events_text='', summary=''):
    """编译事件对话为结构化事件列表"""
    parts = [f"""{_novel_header(title, genre, summary)}

请根据对话设计本次讨论的新事件。

故事大纲：
{outline_content[:1000]}"""]

    if existing_events_text:
        parts.append(existing_events_text)

    parts.append("""输出 JSON 数组：
[
  {
    "title": "事件标题（6-15字）",
    "description": "详细叙述（50-200字）",
    "cause": "前因（引用前一事件结果或初始条件）",
    "effect": "后果（对后续/角色的影响）",
    "related_characters": "关联角色（顿号分隔）"
  }
]

要求：
- 只输出本次对话中的新事件，从对话提取
- 事件间因果连贯
- 不输出 chapter_no 或章节信息""")

    return '\n\n'.join(parts)


# =============================================================================
# 5. 批量生成章节细纲
# =============================================================================

def get_chapter_outlines_prompt(title, genre, outline_content, total_chapters, word_count_per_chapter, summary=''):
    """批量生成所有章节的细纲"""
    return f"""{_novel_header(title, genre, summary)}

基于以下大纲，生成 {total_chapters} 章的章节细纲。

大纲：
{outline_content}

要求：每章 {word_count_per_chapter} 字，包含情节要点、出场角色、关键事件。章节间连贯，节奏有起伏。

JSON 格式：
[
  {{
    "chapter_no": 1,
    "title": "章节标题",
    "content": "细纲内容",
    "word_count": {word_count_per_chapter}
  }}
]"""


# =============================================================================
# 6. 单章细纲
# =============================================================================

def get_single_chapter_outline_prompt(title, genre, outline_content, chapter_no, chapter_title,
                                       prev_outline_content='', next_outline_content='', summary=''):
    """生成单章细纲"""
    parts = [f"""{_novel_header(title, genre, summary)}

为第 {chapter_no} 章生成详细细纲。

大纲：
{outline_content}

章节标题：{chapter_title}"""]

    if prev_outline_content:
        parts.append(f"前一章细纲：\n{prev_outline_content}")
    if next_outline_content:
        parts.append(f"后一章细纲：\n{next_outline_content}")

    reqs = ["生成详细细纲：情节要点、出场角色、关键事件"]
    if prev_outline_content or next_outline_content:
        reqs.append("与前后章节保持连贯")
    reqs.append("内容具体，便于后续生成正文")

    parts.append('\n'.join(f"{i+1}. {r}" for i, r in enumerate(reqs)))
    parts.append("直接输出细纲内容，无需 JSON。")

    return '\n\n'.join(parts)


# =============================================================================
# 7. 重新生成单章细纲
# =============================================================================

def get_regenerate_single_outline_prompt(title, genre, outline_content, chapter_no,
                                          prev_outline_content='', next_outline_content='', summary=''):
    """重新生成单章细纲"""
    parts = [f"""{_novel_header(title, genre, summary)}

重新生成第 {chapter_no} 章的细纲。

大纲：
{outline_content}"""]

    if prev_outline_content:
        parts.append(f"前一章细纲：\n{prev_outline_content}")
    if next_outline_content:
        parts.append(f"后一章细纲：\n{next_outline_content}")

    parts.append("生成详细细纲：情节要点、出场角色、关键事件。")

    return '\n\n'.join(parts)


# =============================================================================
# 8. 事件链生成系统提示词
# =============================================================================

def get_event_chain_system_prompt(title, genre, summary=''):
    """事件链生成的整体指令"""
    return f"""{_novel_header(title, genre, summary)}

你是网文故事架构师，擅长设计因果紧密的事件链。

## 任务
基于大纲生成逻辑严密的事件链。每个事件间必须有明确因果：前一事件的结果 → 后一事件的起因。

## 设计原则
1. 因果递进：A→结果→触发B→结果→触发C
2. 冲突升级：事件严重程度和范围逐步扩大
3. 角色驱动：事件由角色决策或行动推动
4. 伏笔铺垫：早期事件为后期转折铺垫
5. 节奏交替：紧张事件与缓冲事件交替

## 事件结构
- 标题：6-15字，概括核心
- 描述：50-200字，详细叙述
- 前因：为什么会发生（谁做了什么导致）
- 后果：导致了什么（对人物/局势/后续的影响）
- 关联角色：参与的角色（顿号分隔）

## 输出格式
[
  {{
    "event_no": 1,
    "title": "事件标题",
    "description": "事件描述",
    "cause": "前因",
    "effect": "后果",
    "related_characters": "角色A、角色B"
  }}
]"""


# =============================================================================
# 9. 事件链生成附加上下文
# =============================================================================

def get_event_chain_generation_extra(title, genre, outline_content, format_type, summary=''):
    """事件链生成的具体上下文"""
    hint = "长篇15-30个事件" if format_type == 'long' else "短篇5-10个事件"
    return f"""
## 大纲
{outline_content}

要求：{genre}类型，{format_type}（{hint}），因果连贯无断裂。"""


# =============================================================================
# 10. 重新生成单个事件
# =============================================================================

def get_regenerate_event_prompt(title, genre, outline_content, event_no, prev_event_info='',
                                 next_event_info='', current_event_info='', summary=''):
    """重新生成单个事件"""
    parts = [f"""{_novel_header(title, genre, summary)}

重新生成第 {event_no} 个事件。

大纲：
{outline_content}"""]

    if prev_event_info:
        parts.append(f"前一事件：\n{prev_event_info}")
    if next_event_info:
        parts.append(f"后一事件：\n{next_event_info}")
    if current_event_info:
        parts.append(f"当前信息：\n{current_event_info}")

    parts.append("""输出 JSON：
{
    "title": "事件标题",
    "description": "事件描述",
    "cause": "前因",
    "effect": "后果",
    "related_characters": "关联角色"
}""")

    return '\n\n'.join(parts)


# =============================================================================
# 11. 章节正文 — 流程A（章节细纲）
# =============================================================================

def get_chapter_content_chapter_mode_prompt(title, genre, outline_content, detail_content, prev_content,
                                             logic_content, chapter_no, summary=''):
    """章节正文生成 - 章节细纲模式"""
    parts = [f"""{_novel_header(title, genre, summary)}

生成第 {chapter_no} 章正文。

大纲：
{outline_content}

章节细纲：
{detail_content}"""]

    if prev_content:
        parts.append(f"上一章结尾（请衔接）：\n{prev_content}")

    if logic_content:
        parts.append(f"角色逻辑链：\n{logic_content}")

    reqs = [
        "文笔流畅，网文风格",
        "严格按细纲展开情节",
        "角色性格一致，对话符合设定",
        "细节描写丰富",
        "结尾有悬念或转折",
    ]
    if prev_content:
        reqs.insert(2, "与上一章紧密衔接")

    parts.append('\n'.join(f"{i+1}. {r}" for i, r in enumerate(reqs)))

    return '\n\n'.join(parts)


# =============================================================================
# 12. 章节正文 — 流程B（事件驱动）
# =============================================================================

def get_chapter_content_event_mode_prompt(title, genre, outline_content, detail_content, prev_content,
                                           logic_content, chapter_no, summary=''):
    """章节正文生成 - 事件驱动模式"""
    parts = [f"""{_novel_header(title, genre, summary)}

生成第 {chapter_no} 章正文。

大纲：
{outline_content}

本章事件链：
{detail_content}"""]

    if prev_content:
        parts.append(f"上一章结尾（请衔接）：\n{prev_content}")

    if logic_content:
        parts.append(f"角色逻辑链：\n{logic_content}")

    reqs = [
        "文笔流畅，网文风格",
        "完整覆盖所有事件，每个事件充分展开",
        "事件因果逻辑清晰：前因→事件→后果",
        "事件关联角色必须出场",
        "角色性格一致，对话符合设定",
        "细节描写丰富",
        "结尾有悬念或转折",
    ]
    if prev_content:
        reqs.insert(4, "与上一章紧密衔接")

    parts.append('\n'.join(f"{i+1}. {r}" for i, r in enumerate(reqs)))

    return '\n\n'.join(parts)


# =============================================================================
# 13. 角色抽取
# =============================================================================

def get_extract_characters_prompt(title, genre, outline_content, outlines_content='',
                                   chapters_content='', summary=''):
    """从大纲/细纲/章节中抽取角色"""
    prompt = f"""{_novel_header(title, genre, summary)}

请从以下内容提取所有角色。

大纲：
{outline_content}"""

    if outlines_content:
        prompt += f"\n\n细纲/事件：\n{outlines_content}"
    if chapters_content:
        prompt += f"\n\n章节：\n{chapters_content}"

    prompt += """

JSON 格式：
[
  {
    "name": "角色名",
    "gender": "性别",
    "personality": "性格描述",
    "background": "背景故事",
    "goal": "目标动机",
    "relations": [{"target": "其他角色", "relation": "关系描述"}]
  }
]

要求：提取所有角色（主角、配角、反派），根据内容推断信息，综合多来源整理。"""

    return prompt


# =============================================================================
# 14. 角色逻辑链
# =============================================================================

def get_character_logic_chains_prompt(title, genre, outline_content, unit_name, detail_content,
                                       characters_info, mode_hint, summary=''):
    """生成角色逻辑链"""
    return f"""{_novel_header(title, genre, summary)}

根据大纲和{unit_name}数据，为每个角色生成逻辑链。

大纲：
{outline_content}

{unit_name}数据：
{detail_content}

角色：
{characters_info}

为每个角色在每个{unit_name}中生成：
1. 动机：角色为何如此行动（内在驱动 + 外部推动）
2. 变化：经过此{unit_name}后发生了什么改变（心态/能力/关系/目标）

{mode_hint}

JSON 格式：
[
  {{
    "character_name": "角色名",
    "chapter_no": 1,
    "motivation": "动机描述",
    "change": "变化描述"
  }}
]"""


# =============================================================================
# 15. 反推章节细纲
# =============================================================================

def get_reverse_chapter_outline_prompt(title, genre, chapter_title, chapter_content, summary=''):
    """从章节正文反推细纲"""
    return f"""{_novel_header(title, genre, summary)}

从以下章节反推细纲。

标题：{chapter_title}
内容：
{chapter_content}

输出细纲：主要情节点、出场角色、关键事件、情感走向。
直接输出，无需 JSON。"""


# =============================================================================
# 16. 反推大纲（短篇）
# =============================================================================

def get_reverse_outline_short_prompt(title, genre, content, summary=''):
    """从短篇正文反推大纲"""
    return f"""{_novel_header(title, genre, summary)}

从以下短篇内容生成大纲。

内容：
{content}

输出：故事背景、主要情节线、关键转折点、结局。"""


# =============================================================================
# 17. 反推大纲（长篇）
# =============================================================================

def get_reverse_outline_long_prompt(title, genre, outlines_text, summary=''):
    """从章节细纲反推大纲"""
    return f"""{_novel_header(title, genre, summary)}

从各章细纲反推完整大纲。

细纲：
{outlines_text}

输出：故事背景、主要情节线、关键转折点、结局。"""


# =============================================================================
# 18. 反推角色
# =============================================================================

def get_reverse_characters_prompt(title, genre, chapter_title, chapter_content, summary=''):
    """从章节正文反推角色"""
    return f"""{_novel_header(title, genre, summary)}

从以下章节提取所有角色。

标题：{chapter_title}
内容：
{chapter_content}

JSON 格式：
[
  {{
    "name": "角色名",
    "gender": "性别",
    "personality": "性格描述",
    "background": "背景故事",
    "goal": "目标动机"
  }}
]

信息不足可留空。"""
