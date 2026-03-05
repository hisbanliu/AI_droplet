# 变更日志

AI Droplet 的所有重要变更都会记录在此。
格式参考 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)。

---

## [Unreleased]

_未来版本计划_

- 使用 GitHub Actions `cron` 实现全自动每日更新（v2）
- 通过 Giscus 增加用户评论功能（v3）
- 迁移到 Next.js + Vercel，支持 SSR 与用户系统（v4）
- 新增 LMSYS Chatbot Arena 基准榜单模块
- 新增模型基准对比表格

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
