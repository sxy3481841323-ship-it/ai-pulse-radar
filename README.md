# 野生 AI 雷达 · 开源创意工作台与跨项目通用 Skill 宝库

在线网页地址：**[https://sxy3481841323-ship-it.github.io/ai-pulse-radar/](https://sxy3481841323-ship-it.github.io/ai-pulse-radar/)**

这个仓库**并不是「野生 AI 雷达」这一个网页的一次性专用代码库**，它同时承担 **两个核心角色**：

1. **线上网页项目「野生 AI 雷达」**：展示好玩的可视化实盘、一句话讲清价值的极客社群热帖与企业大事记，以及按场景分类的可点开 Skill 宝库。
2. **跨项目、跨 Agent 的通用共享 Skill 母库（`.agents/skills/` + `sync_skills.py`）**：收录了 **26 个**破除传统 AI 套路的网页视觉、物理微交互、生成艺术、3D/Shader 与浏览器游戏开发技能——**供你和协作者以后开任意新游戏、新网站、新创意项目永久复用，而非仅服务于本网页。**

---

## 一、Skill 在仓库里的相对位置，以及怎么用到你以后所有项目里？

### 1. 仓库里的标准相对路径
```text
.agents/skills/<skill-name>/SKILL.md
```
- 只要任何 AI 助手（**Antigravity / Codex / Gemini CLI** 等支持 `.agents/skills/` 发现机制的 Agent）打开本仓库，就会自动识别这 26 个技能。
- 其他助手（**Claude Code / Cursor / Windsurf**）可直接按相对路径 `.agents/skills/<skill-name>/SKILL.md` 读取，或直接同步到本机全局目录让全电脑所有项目永久生效。

### 2. 一键同步到本机全局目录（全电脑所有新项目直接用）
以后你要**另起炉灶做一个全新游戏或全新网站**，不想每次都在新文件夹里重新装一遍 Skill，只需要在本仓库运行一次：

```bash
python3 sync_skills.py
```

脚本会自动探测你本机正在使用的 AI 助手全局目录，把仓库 `.agents/skills/` 下的 26 个技能**补齐到对应的全局位置**：
- **Antigravity**：`~/.gemini/config/skills/<skill-name>/SKILL.md`
- **Claude Code**：`~/.claude/skills/<skill-name>/SKILL.md`
- **Codex**：`~/.codex/skills/<skill-name>/SKILL.md`

同步完成后，你**新建任何游戏或网站工程文件夹**，打开你的 AI 就能直接点名调用全套技能，无需再次安装。

### 3. 双向回传：在别的电脑 / 别的 Agent 上新装了 Skill 怎么办？
如果你或朋友在别的 Agent 上新装了好用的通用设计/游戏开发 Skill，只需在本仓库跑一句回传命令：

```bash
python3 sync_skills.py --push <新技能名称>
```

脚本会自动把本机的新技能拷贝回仓库的 `.agents/skills/<新技能名称>/`（自动过滤 `.git` 并拦截任何疑似密钥），提交推送到 GitHub 后，下次你切回自己电脑或换任何 Agent 接手，都会自动检测并下载补齐。

---

## 二、收录的 26 个通用 Skill（游戏开发 + 反套路网页设计）

| 分类 | 包含技能目录（位于 `.agents/skills/`） | 用途一句话 |
| :--- | :--- | :--- |
| **浏览器游戏开发与玩法策划（9 个）** | `game-brainstorm`、`game-quick-design`、`game-feel`、`level-design`、`game-ui-ux`、`phaser-core`、`threejs-game-director`、`threejs-gameplay-systems`、`threejs-aaa-graphics-builder` | 从零脑暴反套路玩法循环、做 2D/3D 浏览器游戏骨架、注入顿帧/震屏/音效“爽感”与 HUD 界面 |
| **硬核 3D / WebGL / Shader（5 个）** | `threejs-fundamentals`、`threejs-shaders`、`threejs-materials`、`threejs-lighting`、`threejs-postprocessing` | Three.js 场景搭建、PBR 物理材质、HDR 光照、自定义 GLSL Shader 与后期特效 |
| **物理微交互动效与生成艺术（6 个）** | `emil-design-eng`、`animate`、`gestures`、`review-animations`、`algorithmic-art`、`canvas-design` | 弹簧物理惯性、跟手拖拽、可打断过渡动画、p5.js 生成艺术与版画海报设计 |
| **反 AI 塑料感网页审美（6 个）** | `antialgorithm`、`impeccable`、`taste-skill`、`frontend-design`、`ui-ux-pro-max`、`interface-design` | 打破千篇一律圆角渐变 SaaS 模板，实现实体工业、瑞士网格、复古桌面等高定质感 |

> **开新游戏时的推荐启动组合口令**：
> 新建游戏项目文件夹后，直接对你的 AI 说：
> *“先调用全局里的 `game-brainstorm` 和 `antialgorithm` 帮我构思一个反套路的游戏核心机制；确认后再用 `threejs-game-director` + `game-feel`（或 `phaser-core` + `game-feel`）做出带打击感和音效的可玩原型。”*

---

## 三、「野生 AI 雷达」网页本身包含什么？

1. **可视化项目（内联零断连实盘）**：
   - `Astra 6.2` — **H-07 游隼 · 旋翼工坊**（8 大总成三维爆炸拆解 + 飞行遥测）
   - `DeepSeek-V4-Pro` — **三维洛伦兹蝴蝶与奇异吸引子织机**
   - `DeepSeek-V4-Pro` — **旋转六边形弹球（刚体碰撞与切向摩擦）**
   - `DeepSeek-V4-Pro` — **A 股 RSRS/HMM 择时与 Level-2 逐笔订单流沙盘**
   - 联动抓取 Hugging Face Spaces 与 Hacker News Show HN 的社区新奇在线项目。
2. **社群一手热帖 & 企业大事记**：每日抓取 Hacker News、Simon Willison、Lobsters、GitHub 新仓库、V2EX 及 OpenAI / Anthropic / Google / 国内大模型厂商官方发布，用**一句话**直白讲清价值，全部直达原始出处。
3. **可点开的 Skill 宝库**：默认折叠，点开按大学工科、创业、日常生活、量化课实战助手分类速查，附一键复制的提示词与安装命令。

---

## 四、常用维护命令

```bash
# 1. 拉取云端最新更新，并自动把仓库缺失的 Skill 下载补齐到本机
git pull --rebase && python3 sync_skills.py

# 2. 在本机新装了通用 Skill 后，同步回仓库 .agents/skills/
python3 sync_skills.py --push <skill-name>

# 3. 抓取全部一手源并用 DeepSeek 提纯（支持主/备双 Key 自动切换）
python3 fetch_and_digest.py

# 4. 修改 demos/ 或 data/classics.json 后，重打包内联实盘到 data/feed.js
python3 -c 'import json, fetch_and_digest as fd; fd.write_feed(json.load(open(fd.FEED_JSON)))'

# 5. 本地启动静态服务预览网页
python3 -m http.server 8766
```

协作者与跨 Agent 接力规范请务必阅读 [`AGENTS.md`](./AGENTS.md) 与 [`AI_GUIDE.md`](./AI_GUIDE.md)。
