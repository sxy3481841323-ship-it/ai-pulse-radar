# AI 雷达 (AI Pulse Radar)

**一手 AI 社区在玩什么** · 在线访问：**[https://sxy3481841323-ship-it.github.io/ai-pulse-radar/](https://sxy3481841323-ship-it.github.io/ai-pulse-radar/)**

每天自动抓取一手 AI 极客社区（Hacker News、Simon Willison 博客、Lobsters、GitHub 新仓库、Hugging Face Spaces、V2EX）的整活、野生评测与好玩项目，以及国内外大厂（OpenAI、Anthropic、Google / DeepMind、DeepSeek、通义千问 Qwen、Kimi、智谱等）的官方发布，并用 DeepSeek 提纯中文标题与看点。

## 页面模块
1. **今日雷达 (`#radar`)**：
   - **今日一手社区简报**：自动归纳社区最近两天热议的核心脉络，点击引用编号可直接定位到对应原帖卡片。
   - **主信息流**：按「整活 / 好玩」「野生评测」「开源工具 / Demo」「社区热议」分类筛选，所有链接、热度数据、发布日期均来自原始 API / RSS，零人工编造。
   - **右侧栏**：国内外官方发布时间线 + Hugging Face 实时热门模型榜。
2. **经典测试实验室 (`#lab`)**：
   - 收录社区最著名的民间测试（Simon Willison 的**「鹈鹕骑自行车 SVG 测试」**、Flavio Adamo 的**「旋转六边形弹球物理测试」**、以及**「一句话生成伪 3D 公路赛车游戏」**）。
   - 每道题均使用 `make_demos.py` 实际调用 `DeepSeek-V4.1-Flash` 与 `DeepSeek-V4-Pro` 生成并保存在 `demos/` 目录下，可在网页内直接运行试玩、切换模型对比、复制原始 Prompt。

## 本地运行与更新
```bash
# 抓取全部一手源并用 DeepSeek 提纯（需配置 DEEPSEEK_API_KEY）
python3 fetch_and_digest.py

# 重新生成经典测试实验室 Demo
python3 make_demos.py --force
```

给其他 AI 助手的修改说明见 [`AI_GUIDE.md`](./AI_GUIDE.md)。
