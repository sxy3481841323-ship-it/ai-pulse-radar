# AI 雷达 (AI Pulse Radar) · 架构说明与跨 AI 维护指南

> **给其他 AI（Claude / Cursor / ChatGPT / Windsurf / Antigravity）的维护契约**：
> 当用户要求你修改此项目时，请先阅读本文件，保持以下原则和数据结构。

## 1. 核心铁律（严禁违反）
1. **绝不编造链接、热度、日期或出处**：
   - 任何社区条目或官方发布的 `url`、`discuss_url`、`published_at`、`points`、`comments` 必须 100% 来自原始 API / RSS 数据。
   - 在 `fetch_and_digest.py` 中，DeepSeek 模型只能通过整数 `ref` 引用原始条目并撰写中文标题（`title_zh`）、看点解释（`why`）与分类标签，**不允许模型输出任何 URL 或数字**。
2. **所有 Demo 必须真实可访问**：
   - 「经典测试实验室」中的 Demo 存放在 `demos/<classic-id>/<model>.html`，是由 `make_demos.py` 实际调用模型 API 生成并保存在仓库本地的独立 HTML 文件，保证在任何网络环境下 100% 可打开、可交互。
3. **浅色编辑风格 UI**：
   - 样式集中在 `assets/style.css`，采用温暖的纸感浅色主题（`#f6f5f1` 背景 + `#ffffff` 卡片 + `#ea580c` 陶土橙点缀），不要改回暗黑霓虹风。
4. **零前端构建依赖 & 防 XSS**：
   - 纯原生 HTML (`index.html`) + CSS (`assets/style.css`) + JS (`assets/app.js`)。
   - 数据同时写入 `data/feed.json` 和 `data/feed.js`（`window.RADAR = ...`），支持直接双击 `index.html` 打开或通过 GitHub Pages 访问。
   - `assets/app.js` 渲染任何外部字段时必须经过 `esc()` 转义。

## 2. 目录结构
- `index.html`：主页面（包含「今日雷达」「经典测试实验室」「关于」三个视图）
- `assets/style.css`：浅色主题样式表
- `assets/app.js`：前端渲染与交互逻辑
- `fetch_and_digest.py`：并发抓取一手源（Hacker News、Simon Willison、Lobsters、GitHub 新仓库、Hugging Face Spaces、V2EX、OpenAI/Anthropic/Google/DeepMind 官方及 HF 厂商模型发布）并调用 DeepSeek 提纯
- `make_demos.py`：实际调用 DeepSeek 模型运行 `data/classics.json` 中的经典民间测试，将输出保存为 `demos/<id>/<model>.html`
- `data/classics.json`：经典测试定义与实测运行元数据
- `data/feed.json` & `data/feed.js`：抓取与提纯后的完整数据

## 3. 常用命令
```bash
# 1. 抓取全部一手源并用 DeepSeek 提纯（需在环境变量或 .env 中配置 DEEPSEEK_API_KEY）
python3 fetch_and_digest.py

# 2. 仅抓取一手源，不调用大模型
python3 fetch_and_digest.py --no-llm

# 3. 生成或重跑经典测试实验室的真实 Demo
python3 make_demos.py
python3 make_demos.py --force
```
