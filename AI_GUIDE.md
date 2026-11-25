# 野生 AI 雷达 · 架构说明与维护速览 (`AI_GUIDE.md`)

> **跨 Agent / 协作者首要契约已迁移至 [`AGENTS.md`](AGENTS.md)**。
> 在修改任何代码、样式、Prompt 或抓取逻辑前，**请务必先完整阅读 [`AGENTS.md`](AGENTS.md)**（内含最新设计红线、三段式布局规范、内联打包机制、双 Key 故障切换与交接日志）。

## 1. 核心铁律摘要

1. **零伪造一手数据**：`url`、`discuss_url`、`published_at`、`points`、`comments` 必须 100% 来自真实 API / RSS；大模型在 `fetch_and_digest.py` 中只能引用整数 `ref`。
2. **浅色温暖纸张美学**：底色 `#efeee8` / `#fafbf8` + 墨黑 `#181d1a` + 朱砂橙 `#d9481e`，**禁止暗黑模式**；保持舒展呼吸感，**不用 `01/02/03` 序号与多余括号文案**，每条资讯与 Skill 用**一句话讲清价值**。
3. **零断连内联实盘**：`demos/<id>/<model>.html` 会被 `fetch_and_digest.py` 自动内联打包进 `data/feed.js`（`inline_html`），前端通过 `iframe.srcdoc` 与页内全屏/Blob 打开。修改 `demos/` 或 `data/classics.json` 后必须重新打包 `data/feed.js`。
4. **样式/脚本双份同步**：`index.html` 内联了完整 `<style>` 与 `<script>`（防止 Safari 缓存错位），改动后请同步更新 `assets/style.css` 与 `assets/app.js`。
5. **密钥安全**：严禁提交任何 API Key；使用 `.env` 或 GitHub Actions Secrets 中的 `DEEPSEEK_API_KEY` 与 `DEEPSEEK_API_KEY_FALLBACK`（主 Key 耗尽自动切备用 Key）。

## 2. 目录结构

- `AGENTS.md`：**跨 Agent 与朋友协同接力说明书（必读）**
- `index.html`：主页面（内联样式与交互脚本，分「可视化项目」「社群一手热帖 & 企业大事记」「Skill 宝库」三块）
- `assets/style.css` & `assets/app.js`：与 `index.html` 保持同步的样式与前端脚本镜像
- `demos/`：独立单文件可交互实盘 HTML（`helicopter-kestrel/astra-6-2.html`、`chaos-attractor/deepseek-v4-pro.html`、`hexagon-ball/deepseek-v4-pro.html`、`quant-vol-lob/deepseek-v4-pro.html`）
- `fetch_and_digest.py`：纯标准库一手源抓取、DeepSeek 一句话提纯、双 Key 余额检查与自动切换、`feed.js` 内联打包
- `make_demos.py`：调用 DeepSeek API 批量生成 `data/classics.json` 实盘的工具脚本
- `data/classics.json` / `data/feed.json` / `data/feed.js`：实盘配置与抓取提纯数据包
- `.github/workflows/daily_digest.yml`：每日定时自动抓取并推送更新的 GitHub Actions 工作流

## 3. 常用命令

```bash
# 1. 拉取云端最新自动更新（动手前必跑）
git pull --rebase

# 2. 抓取全部一手源并用 DeepSeek 提纯（自动读取 .env 主备 Key）
python3 fetch_and_digest.py

# 3. 仅重打包 classics 内联实盘到 data/feed.js（改完 demos/ 或 classics.json 后必跑）
python3 -c 'import json, fetch_and_digest as fd; fd.write_feed(json.load(open(fd.FEED_JSON)))'

# 4. 仅抓取一手源，不调用大模型
python3 fetch_and_digest.py --no-llm

# 5. 本地启动静态服务预览
python3 -m http.server 8766
```
