# 变更日志

AI Droplet 的所有重要变更都会记录在此。
格式参考 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)。

---

## [0.3.0] — 2026-03-05

### 变更

- **模板拆分重构**：将单一 900 行 `templates/index.html.j2` 拆分为骨架 + 6 个独立 section 文件，解决 PLAN.md 中记录的 v1 可维护性问题 #1。
  - 新增 `templates/sections/news.html.j2`、`models.html.j2`、`mcp.html.j2`、`skills.html.j2`、`ides.html.j2`、`tools.html.j2`
  - `index.html.j2` 精简为骨架文件（847 → 498 行），通过 Jinja2 `{% include %}` 引入各 section
  - 生成产物 `docs/index.html` 功能与外观完全不变（输出验证通过：6 个 section 全部存在）
  - 修正 IDEs 模块 tagline 引号的 HTML 编码问题（`'\"'` → `"<span x-text>"` 内联结构）

### 新增

- `README.md`：项目首页文档，含功能表、快速启动步骤、架构说明、工具收录指南

---

## [Unreleased]

_未来版本计划_

- 使用 GitHub Actions `cron` 实现全自动每日更新（v2）
- 通过 Giscus 增加用户评论功能（v3）
- 迁移到 Next.js + Vercel，支持 SSR 与用户系统（v4）
- 新增 LMSYS Chatbot Arena 基准榜单模块
- 新增模型基准对比表格

---

## [0.2.0] — 2026-03-05

### 变更

- **数据加载架构重构**：从"数据嵌入 HTML"改为"运行时 fetch() 加载"。
  - `generate_site.py` 新增 `copy_data_files()`，将 `data/*.json` 复制到 `docs/data/`
  - `templates/index.html.j2` 所有数据渲染改由 Alpine.js 异步 `fetch()` 驱动，Jinja2 仅传入统计数字
  - `index.html` 体积从 **476 KB → 37 KB**（减少 92%）
  - 浏览器首屏加载更快，各模块数据独立缓存，文件各自可版本化
- 新增 `docs/data/` 目录：`news.json`、`models.json`、`mcp.json`、`skills.json`、`ides.json`、`tools.json` 随 git push 一同发布
- 各页面模块新增 Loading 动画占位符

### 技术决策记录

- 静态站数据公开是必然代价（网站内容本就公开展示）；`.env` API Key 不进 `docs/` 且已被 `.gitignore` 排除。
- `docs/data/` 不手动维护，每次 `generate_site.py` 运行时自动覆盖。

---

## [0.1.0] — 2026-03-04

### 新增

- 项目脚手架：`scripts/`、`data/`、`templates/`、`static/`、`docs/`
- **`scripts/fetch_news.py`**：从 10 个 RSS 源抓取 AI 新闻（OpenAI、Anthropic、Google DeepMind、TechCrunch、The Verge、VentureBeat、arXiv cs.AI、HuggingFace Blog、MIT Tech Review、Hacker News），并使用 Gemini API 进行 0-10 评分与 Top 10 摘要。
- **`scripts/fetch_models.py`**：从 HuggingFace API 拉取高点赞开源模型（`sort=likes`；注：HuggingFace REST API 已不支持 `sort=trending`），并与手工维护的商业模型合并；按 `huggingface_id` 去重。
- **`scripts/fetch_mcp.py`**：抓取并解析 `punkpeye/awesome-mcp-servers` 的 README，生成结构化 MCP Server 目录。
- **`scripts/generate_site.py`**：通过 Jinja2 将 JSON 数据渲染为 `docs/index.html`。
- **`run_daily.py`**：一键执行脚本，支持 `--push`、`--skip-news`、`--skip-models`、`--skip-mcp` 参数。
- **`templates/index.html.j2`**：单页响应式 UI（Tailwind CSS + Alpine.js）。
  模块包含：Daily News、Models、MCP、Agent Skills、AI IDEs、AI Tools。
  功能包含：EN/中 切换、模型搜索+类型过滤+分页、MCP 分类过滤+搜索、工具分类标签页。
- **`static/i18n.js`**：翻译字典源文件（构建时内嵌）。
- **`data/models_curated.json`**：17 个手工维护模型（GPT-4o、o3、Claude 3.7 Sonnet、Gemini 2.0 Flash、Grok 3、Llama 4、DeepSeek-R1、Mistral、Qwen2.5、Phi-4、Gemma 3）。
- **`data/skills.json`**：15 个 Anthropic Agent Skills（手工维护）。
- **`data/ides.json`**：8 个 AI IDE（VS Code+Copilot、Cursor、Windsurf、Zed、JetBrains AI、Replit、Devin、Void）。
- **`data/tools.json`**：18 个 AI 工具，覆盖 6 大分类（图像、视频、音频、搜索、编程、生产力）。
- **`PLAN.md`**：完整项目规划，包含架构、数据来源、i18n 规范、JSON 结构、v1-v4 升级路线。
- **`CHANGELOG.md`**：本文件。
- GitHub Pages 部署源配置为 `docs/` 目录。

### 技术决策记录

- 在手动更新阶段，为了零运维成本，优先选择静态站点（GitHub Pages），而非服务器部署。
- 新闻评分模型选用 Gemini `gemini-2.0-flash`，原因是免费额度高、适合日更场景。
- Pages 源目录选用 `docs/`，便于在同一分支中分离源码与构建产物。
- 翻译字典内嵌到生成后的 HTML 中（不依赖外部 JS），保证单文件可移植性。
- HuggingFace REST API 不支持 `sort=trending`（网站上的 trending 为内部计算指标），改用 `sort=likes`。
- MCP 数据量达到 1294 条，前端增加分页（30 条/页）以保证交互性能。
- `awesome-mcp-servers` README 使用 `### 🛠️ <a name="anchor"></a>Category` 标题格式；解析器通过 `</a>` 作为分割点提取干净分类名。

---

_后续版本发布后，将在此继续追加历史记录。_
