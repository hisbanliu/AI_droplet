# AI Droplet — 项目规划文档

> 版本: v0.2 | 日期: 2026-03-05

## 项目目标

构建一个 AI 信息聚合网站，帮助自己和公众一目了然地了解：当日 AI 新闻、全球主流大模型、MCP 生态、Agent Skills、AI IDE、AI 工具等。

---

## 整体架构

```
每日手动执行
    ↓
Python 脚本（scripts/）
    ↓ 抓取 + LLM 总结
JSON 数据文件（data/）
    ↓ Jinja2 渲染 + 复制 JSON
静态 HTML（docs/index.html）+ docs/data/*.json
    ↓ git push
GitHub Pages（公网访问）
    浏览器 fetch() 按需加载 docs/data/*.json
```

**核心原则**: 无服务器、无数据库、静态托管、手动触发更新（短期），后期可接 GitHub Actions 实现全自动。

---

## 技术选型

| 层       | 技术                               | 理由                           |
| -------- | ---------------------------------- | ------------------------------ |
| 数据采集 | Python + `feedparser` + `httpx`    | Python 基础友好，生态成熟      |
| AI 总结  | Gemini API（`gemini-2.0-flash`）   | 免费额度高，适合每日小批量调用 |
| 前端     | 纯 HTML + Tailwind CSS + Alpine.js | 无需构建工具，vibe coding 友好 |
| 国际化   | 自定义 `i18n.js`（vanilla JS）     | 轻量，无框架依赖               |
| 数据格式 | JSON 文件                          | 静态托管即可，无需数据库       |
| 部署     | GitHub Pages（`docs/` 目录）       | 免费，push 即更新              |

---

## 项目目录结构

```
AI_droplet/
├── PLAN.md                  ← 本文件（项目规划）
├── run_daily.py             ← 一键更新脚本（依次调用所有 fetch 脚本）
├── requirements.txt         ← Python 依赖
├── .env.example             ← 环境变量模板（不含真实密钥）
│
├── scripts/                 ← 数据采集 & 生成脚本
│   ├── fetch_news.py        # 抓取 RSS 新闻 + Gemini 评分总结
│   ├── fetch_models.py      # HuggingFace Trending + 手工维护商业模型
│   ├── fetch_mcp.py         # GitHub awesome-mcp-servers 解析
│   ├── fetch_skills.py      # Anthropic Agent Skills（手工维护）
│   ├── fetch_tools.py       # AI 工具列表（手工维护 + 爬取）
│   ├── fetch_ides.py        # AI IDE 列表（手工维护）
│   └── generate_site.py     # JSON → HTML（Jinja2 渲染）
│
├── data/                    ← 每日生成的 JSON 数据（git 追踪，可查历史）
│   ├── news.json
│   ├── models.json
│   ├── models_curated.json  ← 手工维护的商业模型（OpenAI/Anthropic/Google 等）
│   ├── mcp.json
│   ├── skills.json
│   ├── tools.json
│   └── ides.json
│
├── templates/               ← Jinja2 HTML 模板
│   ├── index.html.j2
│   └── components/
│       ├── news_card.html.j2
│       ├── model_table.html.j2
│       ├── mcp_grid.html.j2
│       ├── skills_list.html.j2
│       ├── ide_cards.html.j2
│       └── tools_tabs.html.j2
│
├── static/                  ← 静态资源
│   └── i18n.js              ← 中英文切换逻辑
│
└── docs/                    ← GitHub Pages 输出目录（不手动编辑，由脚本生成）
    ├── index.html           ← 仅含 UI 框架，~37KB
    └── data/                ← 由 generate_site.py 复制，浏览器 fetch() 加载
        ├── news.json
        ├── models.json
        ├── mcp.json
        ├── skills.json
        ├── ides.json
        └── tools.json
```

> **为什么用 `docs/` 而不是根目录？**
> GitHub Pages 支持"根目录 `/`"或"`docs/` 子目录"两种源，选 `docs/` 是为了在同一分支内分离"源代码（scripts/、templates/）"与"输出产物（HTML）"，保持仓库整洁。
> 未来升级为 GitHub Actions 自动化后，可以改为独立的 `gh-pages` 分支工作流（同样是标准做法，迁移成本低）。

---

## 页面模块规划

### 1. 动态区：昨日 AI 大事件

- **更新频率**: 每日
- **来源（RSS 订阅）**:
  - OpenAI Blog: `https://openai.com/blog/rss.xml`
  - Anthropic Blog: `https://www.anthropic.com/blog/rss.xml`
  - Google DeepMind Blog: `https://deepmind.google/blog/rss.xml`
  - TechCrunch AI: `https://techcrunch.com/category/artificial-intelligence/feed/`
  - The Verge AI: `https://www.theverge.com/ai-artificial-intelligence/rss/index.xml`
  - Hacker News（官方 API）: `https://hacker-news.firebaseio.com/v0/topstories.json`（取 AI 相关条目）
  - arXiv cs.AI: `http://rss.arxiv.org/rss/cs.AI`
- **处理流程**: 抓取过去 24h 内容 → Gemini API 重要性评分（0-10）→ 取 Top 10 → 生成英文一句话摘要（可选生成中文摘要）
- **展示**: 卡片流，含标题 / 来源 / 摘要 / 原文链接

### 2. 大模型列表

- **更新频率**: 每日（自动部分）+ 不定期（手工部分）
- **来源**:
  - HuggingFace API（`/api/models?sort=likes&direction=-1&limit=50&pipeline_tag=text-generation`，
    按最高 likes 排序——注：HuggingFace REST API 已不支持 `sort=trending`，网站 trending 为计算后的内部指标）
  - `data/models_curated.json`（手工维护闭源商业模型：GPT 系列、Claude 系列、Gemini 系列、Grok 等）
- **字段**: 模型名 / 发布方 / 发布时间 / 类型（开源/闭源）/ 主要模态 / 一句话摘要 / 官网链接
- **展示**: 表格 + 搜索框 + 过滤（开源/闭源/多模态等）+ 分页（每页 20 条）

### 3. MCP 列表

- **更新频率**: 每周
- **来源**: GitHub `punkpeye/awesome-mcp-servers`（通过 GitHub API 抓取 README，解析 Markdown 表格）
- **字段**: MCP 名（保留英文）/ 一句话摘要 / 分类 / GitHub 链接
- **展示**: 卡片网格 + 分类过滤

### 4. Agent Skills 列表（Anthropic）

- **更新频率**: 不定期（手工维护）
- **来源**: 手工整理（Anthropic 目前无公开 API）
- **字段**: Skill 名（保留英文原名）/ 一句话英文描述 / 文档链接
- **展示**: 卡片列表
- **注意**: Skill 名称**不翻译**，这是 Anthropic Agent 生态的专有术语

### 5. AI IDE 列表（新增）

- **更新频率**: 不定期（手工维护，变化慢）
- **包含**:
  - VS Code + GitHub Copilot
  - Cursor
  - Windsurf（Codeium）
  - Zed
  - Replit Agent
  - Devin（Cognition）
  - JetBrains AI
  - Void（开源 Cursor 替代）
- **字段**: IDE 名 / 公司 / 核心 AI 特性描述 / 官网链接 / 定价模式（免费/订阅/按量）
- **展示**: 对比卡片

### 6. AI 工具列表（新增）

- **更新频率**: 每周（手工维护）
- **来源**: `data/tools_curated.json`
- **分类**:
  - 图像生成（Midjourney, DALL-E 3, Stable Diffusion, Flux, Ideogram）
  - 视频生成（Sora, Runway Gen-3, Pika, Kling, Hailuo）
  - 音频/音乐（ElevenLabs, Suno, Udio）
  - AI 搜索（Perplexity, You.com, Grok Search）
  - 代码助手（GitHub Copilot, Codeium, Tabnine, Continue）
  - 生产力（Notion AI, ChatGPT, Claude.ai）
- **展示**: 分类标签页 + 卡片

### 7. Benchmark 排行榜（后期 v2）

- **来源**: LMSYS Chatbot Arena（有公开排行数据）
- **展示**: 简版 Elo 排行榜

---

## 国际化（i18n）方案

**默认语言**: 英文
**支持切换**: 中文
**切换方式**: 页面右上角 `EN | 中` 按钮，偏好存入 `localStorage`

**核心原则**:

- UI 框架文字（导航、标签、按钮、提示文字）支持中英切换
- 专有名词（模型名、Skill 名、MCP 名、工具名、IDE 名、新闻标题）**永远保留英文原文，不参与翻译**
- LLM 生成摘要时，英文摘要为必填，中文摘要为可选（`summary_zh` 字段）

**实现示例**:

```javascript
// static/i18n.js
const translations = {
  en: {
    "nav.news": "Daily News",
    "nav.models": "Models",
    "nav.mcp": "MCP",
    "nav.skills": "Agent Skills",
    "nav.ides": "AI IDEs",
    "nav.tools": "AI Tools",
    "news.section_title": "Yesterday's Top AI Events",
    "models.search_ph": "Search models...",
    "models.filter.all": "All",
    "models.filter.open": "Open Source",
    "models.filter.closed": "Closed Source",
  },
  zh: {
    "nav.news": "每日新闻",
    "nav.models": "大模型",
    "nav.mcp": "MCP", // 不翻译
    "nav.skills": "Agent Skills", // 不翻译
    "nav.ides": "AI IDE",
    "nav.tools": "AI 工具",
    "news.section_title": "昨日 AI 大事件",
    "models.search_ph": "搜索模型...",
    "models.filter.all": "全部",
    "models.filter.open": "开源",
    "models.filter.closed": "闭源",
  },
};
```

HTML 中使用 `data-i18n="key"` 属性标记需翻译的元素，切换时由 `i18n.js` 统一替换文本。

---

## 数据 JSON 格式规范

### `news.json`

```json
[
  {
    "id": "2026-03-04-001",
    "title": "OpenAI releases GPT-5",
    "source": "OpenAI Blog",
    "url": "https://openai.com/blog/...",
    "published_at": "2026-03-03T14:00:00Z",
    "summary_en": "OpenAI launched GPT-5 with significantly improved reasoning capabilities.",
    "summary_zh": "OpenAI 发布 GPT-5，推理能力大幅提升。",
    "importance_score": 9.2,
    "tags": ["model-release", "openai"]
  }
]
```

### `models.json`

```json
[
  {
    "name": "GPT-4o",
    "provider": "OpenAI",
    "type": "closed",
    "modality": ["text", "vision", "audio"],
    "released_at": "2024-05-13",
    "summary": "OpenAI's flagship multimodal model with real-time audio and vision.",
    "url": "https://openai.com/gpt-4o",
    "huggingface_id": null
  },
  {
    "name": "Llama 3.3",
    "provider": "Meta",
    "type": "open",
    "modality": ["text"],
    "released_at": "2024-12-06",
    "summary": "Meta's state-of-the-art open source language model.",
    "url": "https://ai.meta.com/blog/meta-llama-3",
    "huggingface_id": "meta-llama/Llama-3.3-70B-Instruct"
  }
]
```

### `ides.json`

```json
[
  {
    "name": "Cursor",
    "company": "Anysphere",
    "tagline": "The AI-first code editor",
    "ai_features": "Inline edit, multi-file context, agent mode, natural language terminal",
    "url": "https://cursor.com",
    "pricing": "Free tier + $20/mo Pro",
    "base": "VS Code fork"
  }
]
```

### `mcp.json`

```json
[
  {
    "name": "filesystem",
    "category": "file-system",
    "summary": "Provides read/write access to local files and directories.",
    "github_url": "https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem",
    "author": "Anthropic"
  }
]
```

---

## 更新流程（手动）

```bash
# 1. 进入项目目录
cd d:\0-sync-code\AI\AI_droplet

# 2. 激活 Python 环境（首次需要创建）
# python -m venv .venv && .venv\Scripts\activate

# 3. 一键更新所有数据并重新生成页面
python run_daily.py

# run_daily.py 内部依次执行：
#   python scripts/fetch_news.py       → data/news.json
#   python scripts/fetch_models.py     → data/models.json
#   python scripts/fetch_mcp.py        → data/mcp.json
#   python scripts/generate_site.py    → docs/index.html
#   git add data/ docs/
#   git commit -m "data: update YYYY-MM-DD"
#   git push
```

---

## 后期升级路径

| 阶段           | 内容                                                      | 触发条件     |
| -------------- | --------------------------------------------------------- | ------------ |
| **v1（当前）** | 手动运行脚本，GitHub Pages 静态托管                       | 现在开始     |
| **v2**         | GitHub Actions `cron` 定时任务（每天 UTC 00:00 自动更新） | 网站稳定后   |
| **v3**         | 评论/收藏功能（Giscus 基于 GitHub Discussions）           | 有持续用户时 |
| **v4**         | 迁移到 Next.js + Vercel，支持服务端渲染、用户系统、搜索   | 流量增长后   |

---

## 环境变量

```bash
# .env（本地使用，不提交到 git）
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_TOKEN=your_github_pat_here    # 用于 GitHub API 避免限流（60次/h → 5000次/h）
```

---

## 开发启动顺序（推荐）

1. 初始化 git 仓库，推到 GitHub，配置 Pages 指向 `docs/` 目录
2. 创建 `requirements.txt` 和 Python 虚拟环境
3. **先跑通最小闭环**: `fetch_news.py` + 手写一个最简 `docs/index.html`，验证新闻卡片可以展示
4. 添加 `generate_site.py`（Jinja2 模板渲染），替换手写 HTML
5. 逐步添加模块：models → mcp → skills → ides → tools
6. 最后加 i18n、搜索/过滤、分页等交互功能

---

## v2 架构规划（迭代路线图）

> 当前 v1 适合 ≤8 个大分类、≤100 条工具条目的规模。
> 分类继续增长时，以下改进应列入优先队列。

### 当前 v1 的可维护性问题

| 问题 | 当前状态 | 规模增大后的风险 |
|------|---------|----------------|
| 单一 900+ 行模板 | 6 个分类 | 新增 5 个分类后 → 1500+ 行，难以审查和调试 |
| `tools.json` 一文件多分类 | 18→32 工具 / 8 子类 | 50+ 条目后查找困难，git diff 噪音大 |
| i18n 翻译硬编码在模板 JS | ~200 行字典 | 每加分类都须改模板而不是只改数据 |
| `generate_site.py` 硬编码 DATA_FILES | 手动列表 | 每新增 JSON 文件需手工改代码 |
| 导航 tabs 硬编码 | 6 项数组 | 每加大分类须改模板 JS |

### v2 目标架构

```
data/
  manifest.json          ← ★ 核心：所有 section/分类的注册表
  sections/              ← 新增的大分类（独立文件）
    agents.json
    writing.json
    research.json
  tools/                 ← tools 细分（取代单一 tools.json）
    image-gen.json
    video-gen.json
    audio.json
    coding.json
    productivity.json
    ai-agents.json       ← 从 tools.json 拆出
    writing.json         ← 从 tools.json 拆出
  i18n/
    en.json              ← 翻译文件独立，模板无翻译字典
    zh.json

templates/
  base.html.j2           ← 只含 <head>、<nav>、<footer>、JS 基础设施
  macros/                ← 每种 section 类型一个 macro 文件
    section_news.html
    section_models.html
    section_mcp.html
    section_tools.html   ← 通用工具 section（可复用）
    section_generic.html ← 新分类的默认模板

docs/
  index.html             ← 由 generate_site.py 生成
  data/
    manifest.json        ← 浏览器读取，动态构建导航 + section
    sections/
    tools/
    i18n/
```

### manifest.json 驱动机制

```json
{
  "version": 2,
  "sections": [
    { "id": "news",    "type": "news",    "file": "news.json",          "nav_key": "nav.news",    "order": 1 },
    { "id": "models",  "type": "models",  "file": "models.json",        "nav_key": "nav.models",  "order": 2 },
    { "id": "mcp",     "type": "mcp",     "file": "mcp.json",           "nav_key": "nav.mcp",     "order": 3 },
    { "id": "skills",  "type": "skills",  "file": "skills.json",        "nav_key": "nav.skills",  "order": 4 },
    { "id": "ides",    "type": "ides",    "file": "ides.json",          "nav_key": "nav.ides",    "order": 5 },
    { "id": "tools",   "type": "tools",   "file": "tools/",             "nav_key": "nav.tools",   "order": 6,
      "subcategories": ["image-gen", "video-gen", "audio", "coding", "productivity", "ai-agents", "writing"] }
  ]
}
```

**优点：**
- 新增分类 = 新建 JSON 文件 + manifest 加一行 → **零改模板代码**
- `generate_site.py` 读 manifest 自动 copy 所有文件
- 浏览器读 manifest 动态构建导航和 section 组件
- i18n 文件独立，翻译可交给贡献者，无需改模板

### 迁移策略（渐进式，不破坏 v1）

**阶段 1（已完成 - v0.2）：**
- [x] 扩展 `tools.json` 加入 `ai-agents`（7 个工具，含 OpenClaw）和 `writing`（7 个工具）
- [x] 模板翻译字典加入新分类 key
- toolsApp() 已是数据驱动，自动识别新分类 → 零代码改动

**阶段 2（优先级：中）：**
- [ ] 新建 `data/manifest.json`，`generate_site.py` 读取它来决定复制哪些文件
- [ ] 提取 i18n 到 `data/i18n/en.json` + `data/i18n/zh.json`，模板用 fetch 加载
- [ ] 把 `templates/index.html.j2` 的 section 代码拆成 Jinja2 macros

**阶段 3（优先级：低，数据量大时启动）：**
- [ ] 按大分类拆分 `tools.json` → `tools/` 子目录
- [ ] 增加 GitHub Actions 自动化（每日定时调用 `run_daily.py --push`）
- [ ] 考虑 Service Worker 离线缓存，提升重复访问性能

