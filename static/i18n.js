/**
 * i18n.js — Source of truth for all UI translations.
 *
 * NOTE: This file is the canonical reference.
 *       The actual translations are EMBEDDED into docs/index.html
 *       by generate_site.py (via the Jinja2 template).
 *       If you add new keys here, also update templates/index.html.j2.
 *
 * Rules:
 *   - Translate UI chrome (nav, labels, buttons, help text)
 *   - NEVER translate proper nouns: model names, MCP names, Skill names,
 *     tool names, IDE names, company names, article titles
 */

const TRANSLATIONS = {
  en: {
    // Hero
    "hero.title": "Your Daily AI Intelligence",
    "hero.subtitle":
      "Models, tools, news, MCP servers, and agent skills — all in one place, updated daily.",
    "hero.stat.news": "top stories today",
    "hero.stat.models": "models tracked",

    // Navigation
    "nav.news": "Daily News",
    "nav.models": "Models",
    "nav.mcp": "MCP", // Do NOT translate
    "nav.skills": "Agent Skills", // Do NOT translate
    "nav.ides": "AI IDEs",
    "nav.tools": "AI Tools",

    // News section
    "news.read_more": "Read →",
    "news.empty": "No news loaded yet.",
    "news.empty_hint": "Run: python scripts/fetch_news.py",

    // Models section
    "models.search_ph": "Search models...",
    "models.total": "total",
    "models.col.name": "Model",
    "models.col.provider": "Provider",
    "models.col.type": "Type",
    "models.col.released": "Released",
    "models.col.summary": "Summary",
    "models.filter.all": "All",
    "models.filter.open": "Open Source",
    "models.filter.closed": "Closed Source",
    "models.no_results": "No models match your search.",
    "models.showing": "Showing",
    "models.of": "of",

    // MCP section
    "mcp.search_ph": "Search MCP servers...",
    "mcp.all_categories": "All categories",
    "mcp.empty": "No MCP servers loaded yet.",
    "mcp.empty_hint": "Run: python scripts/fetch_mcp.py",
    "mcp.no_results": "No servers match your search.",

    // Skills section
    "skills.docs": "Docs →",

    // IDEs section
    "ides.ai_features": "AI Features",
    "ides.visit": "Visit →",
    "ides.base": "Based on",

    // Tools section
    "tools.visit": "Visit →",
    "tools.cat.image-generation": "Image Generation",
    "tools.cat.video-generation": "Video Generation",
    "tools.cat.audio": "Audio & Music",
    "tools.cat.ai-search": "AI Search",
    "tools.cat.coding": "Coding",
    "tools.cat.productivity": "Productivity",

    // Pagination
    "pagination.prev": "Prev",
    "pagination.next": "Next",

    // Footer
    "footer.generated": "Generated",
    "footer.data_sources": "Data sources",
  },

  zh: {
    // Hero
    "hero.title": "你的每日 AI 情报站",
    "hero.subtitle":
      "模型、工具、新闻、MCP 服务器和 Agent Skills —— 一站掌握，每日更新。",
    "hero.stat.news": "条今日精选",
    "hero.stat.models": "个模型收录",

    // Navigation
    "nav.news": "每日新闻",
    "nav.models": "大模型",
    "nav.mcp": "MCP", // 不翻译
    "nav.skills": "Agent Skills", // 不翻译
    "nav.ides": "AI IDE",
    "nav.tools": "AI 工具",

    // News section
    "news.read_more": "阅读全文 →",
    "news.empty": "暂无新闻数据。",
    "news.empty_hint": "运行: python scripts/fetch_news.py",

    // Models section
    "models.search_ph": "搜索模型...",
    "models.total": "个模型",
    "models.col.name": "模型",
    "models.col.provider": "发布方",
    "models.col.type": "类型",
    "models.col.released": "发布时间",
    "models.col.summary": "简介",
    "models.filter.all": "全部",
    "models.filter.open": "开源",
    "models.filter.closed": "闭源",
    "models.no_results": "没有匹配的模型。",
    "models.showing": "显示",
    "models.of": "/",

    // MCP section
    "mcp.search_ph": "搜索 MCP 服务器...",
    "mcp.all_categories": "全部分类",
    "mcp.empty": "暂无 MCP 数据。",
    "mcp.empty_hint": "运行: python scripts/fetch_mcp.py",
    "mcp.no_results": "没有匹配的服务器。",

    // Skills section
    "skills.docs": "文档 →",

    // IDEs section
    "ides.ai_features": "AI 功能",
    "ides.visit": "访问 →",
    "ides.base": "基于",

    // Tools section
    "tools.visit": "访问 →",
    "tools.cat.image-generation": "图像生成",
    "tools.cat.video-generation": "视频生成",
    "tools.cat.audio": "音频 & 音乐",
    "tools.cat.ai-search": "AI 搜索",
    "tools.cat.coding": "代码助手",
    "tools.cat.productivity": "生产力",

    // Pagination
    "pagination.prev": "上一页",
    "pagination.next": "下一页",

    // Footer
    "footer.generated": "生成于",
    "footer.data_sources": "数据来源",
  },
};
