# AI 极客雷达 (AI Pulse Radar) - 跨 AI 协作与维护规范 (`AI_GUIDE.md`)

> **给其他 AI 助手（Claude / Cursor / ChatGPT / Windsurf / Antigravity）的特别说明**：
> 当用户要求你修改此项目（如增加卡片、修改样式、增加抓取源）时，请遵循以下极简架构契约：

## 1. 极简零依赖架构
- **前端界面 (`index.html`)**：单文件纯原生 HTML + CSS + Vanilla JS，无 Webpack/Vite/React 编译步骤，方便用户随时在本地直接打开或托管到 GitHub Pages。
- **双模数据源 (`data/feed.js` 与 `data/feed.json`)**：
  - 为了让用户既能直接双击 `index.html`（`file://` 协议无法 `fetch` 本地 JSON）又能通过 HTTP 访问，`index.html` 通过 `<script src="./data/feed.js"></script>` 读取 `window.AI_RADAR_DATA`。
  - 每次修改数据或运行 `python3 fetch_and_digest.py` 时，请确保 `data/feed.js` 和 `data/feed.json` 保持同步。

## 2. 卡片数据结构契约 (`community_projects` 数组项)
```json
{
  "id": "unique-slug-id",
  "title": "项目中文标题",
  "category": "benchmark | game | fun | tool",
  "category_label": "#野生基准测试 | #一镜到底/3A小游戏 | #极客整活 | #开源神仙小玩具",
  "source_name": "来源社区 (如 Simon Willison's Blog / Reddit r/LocalLLaMA)",
  "source_url": "https://一手原帖地址",
  "demo_url": "https://在线试玩或演示地址",
  "published_at": "发布时间或标签",
  "heat_score": "🔥 热度描述",
  "model_tested": "被测试或使用的模型",
  "tldr": "一句话极客看点（大白话解释它好玩在哪、测出了什么水位）",
  "svg_preview": "可选：内联 <svg>...</svg> 预览代码",
  "prompt_recipe": "复现秘籍：可直接复制的测试 Prompt 或玩法说明",
  "tags": ["标签1", "标签2"]
}
```

## 3. 安全准则
- **严禁**将用户的 `DEEPSEEK_API_KEY` 硬编码进 `index.html`、`data/feed.js` 或任何会被 Git 追踪的文件中。
- 本地运行请放在 `.env`（已被 `.gitignore` 忽略），GitHub Actions 定时运行请使用仓库的 `secrets.DEEPSEEK_API_KEY`。
