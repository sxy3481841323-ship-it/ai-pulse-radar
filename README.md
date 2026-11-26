# 野生 AI 雷达 · 开源创意工作台与跨项目通用 Skill 宝库

在线网页地址：**[https://sxy3481841323-ship-it.github.io/ai-pulse-radar/](https://sxy3481841323-ship-it.github.io/ai-pulse-radar/)**

这个仓库**并不是「野生 AI 雷达」这一个网页的一次性专用代码库**，它同时承担 **两个核心角色**：

1. **线上网页项目「野生 AI 雷达」**：展示好玩的可视化实盘、一句话讲清价值的极客社群热帖与企业大事记，以及按场景分类的可点开 Skill 宝库。
2. **跨项目共享技能库入口**：通用创意、设计、动效、3D 和游戏技能集中维护于独立的 `agent-skills` 仓库；本项目保留同步入口与自身业务规则。

---

## 一、跨项目共享技能库

通用技能统一维护于 [agent-skills](https://github.com/sxy3481841323-ship-it/agent-skills)，本机与三个项目平级。完整目录见共享库 `CATALOG.md`，机器可读索引为 `registry.json`。

```bash
python3 sync_skills.py --agent antigravity
# Codex：python3 sync_skills.py --agent codex
# Claude Code：python3 sync_skills.py --agent claude-code
```

同名内容不同会提示冲突并保留本地副本。新装通用技能必须完整回传共享库，更新索引并保存，再同步到 Agent 的全局目录。读取 GitHub 上的 SKILL.md 可以参考方法；自动发现和使用配套资源需要下载完整目录。

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
git pull --rebase && python3 sync_skills.py --agent antigravity

# 2. 在本机新装了通用 Skill 后，回传到平级的 agent-skills 共享库
python3 sync_skills.py --import <skill-name> --source <本机技能根目录>

# 3. 抓取全部一手源并用 DeepSeek 提纯（支持主/备双 Key 自动切换）
python3 fetch_and_digest.py

# 4. 修改 demos/ 或 data/classics.json 后，重打包内联实盘到 data/feed.js
python3 -c 'import json, fetch_and_digest as fd; fd.write_feed(json.load(open(fd.FEED_JSON)))'

# 5. 本地启动静态服务预览网页
python3 -m http.server 8766
```

协作者与跨 Agent 接力规范请务必阅读 [`AGENTS.md`](./AGENTS.md) 与 [`AI_GUIDE.md`](./AI_GUIDE.md)。
