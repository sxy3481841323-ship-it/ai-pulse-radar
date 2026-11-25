# 野生 AI 雷达 · 跨 Agent 协作与接力说明书 (`AGENTS.md`)

> **给所有接手本项目的 AI Agent（Antigravity / Codex / Claude Code / Cursor / 协作者的 Agent）**：
> 动手改任何文件前，请先通读本说明书与最近 5 条 `git log`，并先执行 `git pull --rebase` 同步云端最新数据。

---

## 1. 项目定位

- **项目名称**：野生 AI 雷达
- **线上地址**：`https://sxy3481841323-ship-it.github.io/ai-pulse-radar/`
- **仓库地址**：`https://github.com/sxy3481841323-ship-it/ai-pulse-radar`
- **目标读者与初衷**：面向喜欢**玩 AI** 的工科大学生与独立开发者。绕开二手自媒体信息差，在一张清爽的网页里看**好玩的可视化实盘、直白的一手极客热帖与企业大事记、以及点开即用的实用 Skill**。

---

## 2. 用户审美与内容红线（严禁破坏）

1. **严格浅色温暖纸张编辑部风格 — 绝对禁止暗黑模式**：
   - 背景底色 `#efeee8`、卡片亮纸 `#fafbf8`、暖灰 `#f3f2ec`、墨黑主文/边框 `#181d1a`、朱砂橙 `#d9481e`、松绿 `#196b48`、钴蓝 `#1b4fa0`。
   - 不要改成暗黑霓虹风、不要搞廉价紫蓝渐变 SaaS 卡片风。
2. **保持舒展、宽敞、呼吸感排版**：
   - 留白充足，避免高密度信息墙或过度压缩导致视觉窒息。
3. **标题与文案禁忌**：
   - 网站主标题与导航**不要带「量化」字样**（保持「野生 AI 雷达」）。
   - **不要带 `01 / 02 / 03` 目录序号**。
   - **不要添加累赘括号说明**（例如已明确删掉的 `（每周推陈出新）`、`（大学、生活、创业、量化课）` 等；Skill 按钮文案保持简洁的「打开 Skill 宝库」）。
4. **一句话讲清价值（禁止堆砌黑话）**：
   - **社群热帖**与**企业大事记**每条必须用**一句话大白话**直接说清「它能干嘛 / 好玩在哪 / 价值在哪」。
   - **Skill 宝库**里的每个 Skill 必须用一句话讲明「方便在哪 / 高效在哪」。
5. **已淘汰内容禁区（禁止加回）**：
   - 不要加回**鹈鹕骑车**（含报头印章）、**赛车游戏**，也不要加回 `DeepSeek-V4.1-Flash` 的 Demo 对比。DeepSeek 实盘仅保留 `DeepSeek-V4-Pro`。
   - **不要放入晦涩的华尔街衍生品数学天书**（如 Heston 偏微分方程等超出用户背景的内容）。若涉及量化，请严格贴合用户已学的 **Python (NumPy/Pandas) 多因子清洗/ICIR、XGBoost/HMM/RSRS/卡尔曼、Level-2 逐笔订单流** 水平。
6. **零伪造数据铁律**：
   - 所有社区条目和官方发布的 `url`、`discuss_url`、`published_at`、`points`、`comments` 必须 100% 来自真实一手 API / RSS。在 `fetch_and_digest.py` 中，大模型只能用 `ref` 整数索引引用，严禁编造 URL 或数字。

---

## 3. 当前页面三段式结构与文件地图

### 页面布局顺序（由上至下）
1. **可视化项目（Playground）**：
   - 4 张精致矢量预览卡片 + 内联交互试玩画布（支持页内全屏模态框 & Blob 新标签页打开）：
     1. `demos/helicopter-kestrel/astra-6-2.html`：`Astra 6.2` — H-07 游隼 · 旋翼工坊（8 总成三维拆解与飞行遥测）
     2. `demos/chaos-attractor/deepseek-v4-pro.html`：`DeepSeek-V4-Pro` — 三维洛伦兹蝴蝶与奇异吸引子织机
     3. `demos/hexagon-ball/deepseek-v4-pro.html`：`DeepSeek-V4-Pro` — 旋转六边形弹球（刚体碰撞与切向摩擦）
     4. `demos/quant-vol-lob/deepseek-v4-pro.html`：`DeepSeek-V4-Pro` — A 股 RSRS/HMM 择时与 Level-2 逐笔订单流沙盘
   - 下方联动展示从 Hugging Face Spaces / Hacker News Show HN 抓来的「社区新冒出来的网页 & 在线 Space」。
2. **社群一手热帖 & 企业大事记**：
   - 左栏：极客社群一手热帖（分类筛选 + 搜索 + 一句话价值高亮框）。
   - 右栏：AI 企业大事记（OpenAI / Anthropic / Google DeepMind / 国内大模型厂官方发布，一句话点明价值）。
3. **Skill 宝库（默认折叠的可点开专区）**：
   - 点击顶部/底部「打开 Skill 宝库」按钮展开。
   - 包含 4 个实用分类：大学工科与课业、创业与独立开发、日常生活便利、用户的量化课实战助手（含 31 讲个人学习画像「自报家门」一键复制器）。

### 核心文件清单与同步规则
- [index.html](index.html)：主页面。**重要工程约定**：为防止 macOS Safari 加载旧的外部 CSS/JS 缓存，`<style>` 和 `<script>` **全部内联写在 `index.html` 中**；如修改样式或脚本，请同步更新 [assets/style.css](assets/style.css) 与 [assets/app.js](assets/app.js) 保持一致。
- [fetch_and_digest.py](fetch_and_digest.py)：仅依赖 Python 标准库的抓取与 DeepSeek 提纯脚本。
  - **双 API Key 自动耗尽切换**：依次读取 `DEEPSEEK_API_KEY`（主额度）与 `DEEPSEEK_API_KEY_FALLBACK`（备用额度），启动时检查余额并在遇到 `HTTP 401/402` 或连续失败时无缝切换至备用 Key，绝不把真实密钥写入跟踪文件。
  - **实盘 HTML 内联打包**：生成 `data/feed.js` 时会自动读取 `data/classics.json` 里每个 Demo 的 HTML 源码写入 `inline_html` 字段；前端通过 `iframe.srcdoc` 与 `Blob` 打开，彻底避免任何网络或路径引起的 `not connected` 报错。
  - **重要维护规则**：修改 `data/classics.json` 或任何 `demos/**/*.html` 后，**必须重新打包 `data/feed.js`**，否则前端内联展示的还是旧源码：
    ```bash
    python3 -c 'import json, fetch_and_digest as fd; fd.write_feed(json.load(open(fd.FEED_JSON)))'
    # 或者完整重抓：
    python3 fetch_and_digest.py
    ```
- `data/classics.json`：4 个主打可视化项目的元数据、操作要点与完整 Prompt。
- `data/feed.json` & `data/feed.js`：实时抓取与提纯结果（`feed.js` 赋值 `window.RADAR`，支持本地直接双击 `index.html` 打开）。
- `.github/workflows/daily_digest.yml`：每天 UTC 00:00（北京时间 08:00）自动运行 `python3 fetch_and_digest.py` 并提交更新 `data/feed.js` 与 `data/feed.json`（使用仓库 Secrets 中的 `DEEPSEEK_API_KEY` 与 `DEEPSEEK_API_KEY_FALLBACK`）。
- `.agents/skills/`：仓库内置共享 Skill 宝库（共 26 个高定网页 UI、物理微交互、生成艺术、3D/Shader、浏览器游戏开发技能，克隆仓库后自动生效）。

---

## 4. 仓库内置共享 Skills（`.agents/skills/`，开箱即用）

本仓库已在根目录 `.agents/skills/` 同步内置了 **26 个破除传统 AI 套路的网页设计与游戏开发 Skill**。
- **如果你使用的是 Antigravity**：将本仓库设成工作区后会自动发现并按需加载这些技能，无需任何额外配置。
- **如果你使用的是 Claude Code / Codex / Cursor / Windsurf**：执行任务前请根据需要直接读取对应 `.agents/skills/<skill-name>/SKILL.md` 及同目录下的 `references/`。

### 26 个共享技能分类速查
1. **反 AI 塑料感网页审美与 UI 设计（6 个）**：
   - `antialgorithm`（破除默认平庸创意大脑）、`impeccable`（含 `/bolder` `/quieter` `/polish` `/delight` `/overdrive` `/critique` 等 48 份风格调教手册）、`taste-skill`（`design-taste-frontend`，三旋钮高定前端）、`frontend-design`（去 AI 味前端结构规范）、`ui-ux-pro-max`（配色/字体/风格词典检索）、`interface-design`（功能型工具面板一致性）。
2. **治好“静态 PPT 感”与生成艺术（6 个）**：
   - `emil-design-eng`、`animate`、`gestures`、`review-animations`（Emil Kowalski 弹簧物理惯性、300ms 内跟手微交互与 1:1 拖拽）、`algorithmic-art`（p5.js 流场与数学视觉奇观）、`canvas-design`（版画/海报视觉构图）。
3. **硬核 3D / WebGL / GLSL Shader（5 个）**：
   - `threejs-fundamentals`、`threejs-shaders`、`threejs-materials`、`threejs-lighting`、`threejs-postprocessing`。
4. **浏览器创意游戏开发、打击爽感与玩法策划（9 个）**：
   - `threejs-game-director`、`threejs-gameplay-systems`、`threejs-aaa-graphics-builder`、`phaser-core`、`game-feel`（顿帧/震屏/粒子/音效爽感）、`level-design`、`game-ui-ux`、`game-brainstorm`（反套路玩法机制脑暴）、`game-quick-design`。

### 推荐协同组合用法
- **打磨网页视觉与实体把玩感**：`antialgorithm` + `impeccable` + `emil-design-eng`
- **制作浏览器创意小游戏**：`game-brainstorm` + `game-feel` + `threejs-gameplay-systems`（或 `phaser-core`）

---

## 5. 跨 Agent / 协作者接力工作流

1. **接手第一步（同步云端）**：
   - 先运行 `git pull --rebase`（因为 GitHub Actions 每天会自动提交 `data/feed.js` 和 `data/feed.json`，不先拉取会 push 被拒）。
   - 查看最近提交：`git log -n 5 --oneline`。
2. **安全开干（建议分支修改）**：
   - 较大改动建议先切新分支（如 `git checkout -b feat/xxx`）；小修改若改崩随时 `git revert` / `git reset` 回滚。
   - **密钥安全铁律**：严禁把任何 `sk-...` 或 `ghp_...` 写入任何被 Git 跟踪的文件；本地开发统一放在已被 `.gitignore` 忽略的 `.env` 中。
3. **改完必须本地验证再推送**：
   - 启动本地服务预览：`python3 -m http.server 8766` 并打开 `http://localhost:8766/` 检查页面排版、控制台无报错、实盘 `srcdoc` 与全屏弹窗可正常打开、Skill 宝库可展开。
   - 若改了 `demos/` 或 `data/classics.json`，务必重新打包 `data/feed.js`。
   - 若改了 `index.html` 内的 `<style>` 或 `<script>`，同步写入 `assets/style.css` 与 `assets/app.js`。
   - 推送前自查：`grep -rn "sk-" . --exclude=".env" --exclude-dir=".git"`（注意 `.sk-` 开头的 CSS class 正常，确认没有真实 API Key）。
4. **更新本文件底部的「交接日志」**，记录改了什么、验证了什么、下一棒需要注意什么，然后 `git commit && git push`。

---

## 交接日志（Handoff Log）

- **2026-11-25（当前基准版本 · 含共享 `.agents/skills/`）**：
  - 已完成三段式舒展浅色排版：可视化项目（4 个内联零断连实盘：`Astra 6.2` 直升机拆解、洛伦兹蝴蝶、六边形弹球、A股 RSRS/HMM+L2 沙盘）→ 社群热帖 & 企业大事记（全量一句话价值）→ 可点开「Skill 宝库」。
  - 已按用户反馈清理所有 `01/02/03` 序号、标题中的「量化」字样以及多余括号文案。
  - 已将 26 个高定网页 UI、微交互动效、生成艺术、3D/Shader 与浏览器游戏开发 Skills 同步打包至仓库 `.agents/skills/`（剔除了 `.git` 与个人量化技能），任意协作者或 Agent 克隆仓库即可直接共享调用。
  - 已接入主/备 DeepSeek API Key 自动切换（`DEEPSEEK_API_KEY` → `DEEPSEEK_API_KEY_FALLBACK`），本地 `.env` 与 GitHub Actions Secrets 已就绪。
  - 下一位 Agent 接手时注意：保持极简、浅色纸感、一句话大白话和内联零断连机制，改完记得重打包 `data/feed.js` 并同步 `assets/`。
