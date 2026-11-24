#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
野生 AI 雷达 · 每周好玩项目 + 一句话极客情报 + 实用 Skill 专区
==============================================================
用法：
    python3 fetch_and_digest.py            # 抓取全部来源并用 DeepSeek 提纯（需要 DEEPSEEK_API_KEY）
    python3 fetch_and_digest.py --no-llm   # 只抓取，不调用模型
"""

import hashlib
import html
import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
FEED_JSON = os.path.join(DATA_DIR, "feed.json")
FEED_JS = os.path.join(DATA_DIR, "feed.js")
CLASSICS_JSON = os.path.join(DATA_DIR, "classics.json")

UA = "ai-radar/4.0 (+https://github.com/sxy3481841323-ship-it/ai-pulse-radar)"
NOW = datetime.now(timezone.utc)
ISO_YEAR, ISO_WEEK, _ = NOW.isocalendar()
WEEK_LABEL = f"{ISO_YEAR}年第{ISO_WEEK}周"
DIGEST_MODEL = os.environ.get("RADAR_MODEL", "deepseek-flash")
COMMUNITY_KEEP_DAYS = 10
COMMUNITY_MAX = 60
OFFICIAL_KEEP_DAYS = 30
OFFICIAL_MAX = 30
SSL_CTX = ssl.create_default_context()


def load_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    env_path = os.path.join(ROOT, ".env")
    if not key and os.path.exists(env_path):
        for line in open(env_path, encoding="utf-8"):
            if line.strip().startswith("DEEPSEEK_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    return key


def http(url, headers=None, data=None, timeout=25):
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h, data=data, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
        return resp.read().decode("utf-8", errors="replace")


def http_json(url, headers=None):
    return json.loads(http(url, headers))


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_time(s) -> datetime:
    if isinstance(s, (int, float)):
        return datetime.fromtimestamp(s, tz=timezone.utc)
    s = (s or "").strip()
    try:
        return parsedate_to_datetime(s).astimezone(timezone.utc)
    except Exception:
        pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return NOW


def clean(text, limit=400) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def recent(dt: datetime, days: float) -> bool:
    return dt >= NOW - timedelta(days=days)


def make_id(url: str) -> str:
    norm = re.sub(r"^https?://(www\.)?", "", (url or "").strip().rstrip("/")).lower()
    return hashlib.sha1(norm.encode()).hexdigest()[:12]


def item(**kw):
    kw.setdefault("points", None)
    kw.setdefault("comments", None)
    kw.setdefault("discuss_url", None)
    kw.setdefault("snippet", "")
    kw["id"] = make_id(kw["url"])
    return kw


# ----------------------------------------------------------------------------
# 实用 Skill 宝库（四大方向：大学工科科研 / 创业独立开发 / 日常生活便利 / 接地气量化实战）
# 每条必须一句话简洁明了说明「方便在哪 / 高效在哪」
# ----------------------------------------------------------------------------
PRACTICAL_SKILLS_SEEDS = [
    # 1. 大学工科与科研
    {
        "repo": "microsoft/markitdown",
        "group": "college",
        "group_label": "🎓 大学工科与课业",
        "badge": "课件/论文秒转 Markdown",
        "title_zh": "MarkItDown · 把老师发的 PPT / PDF / Word / Excel 一键转成 AI 易读笔记",
        "one_sentence": "把散乱的工科课件 PPT、PDF 论文和实验数据表一键转成干净的 Markdown，直接丢给 AI 提炼期末考点或写实验报告。",
        "install_cmd": "pip install markitdown",
        "prompt_recipe": "我已经用 markitdown 把这门课的 PPT 和实验指导书转成了 Markdown。请按「核心公式物理意义 → 常考题型推导步骤 → 实验容易踩坑的边界条件」帮我整理一份一页纸复习速查表。"
    },
    {
        "repo": "typst/typst",
        "group": "college",
        "group_label": "🎓 大学工科与课业",
        "badge": "替代 LaTeX 写公式报告",
        "title_zh": "Typst · 比 LaTeX 简单 10 倍、毫秒级预览的工科报告与数学公式排版神器",
        "one_sentence": "写工科课程大作业、数学公式推导和课程论文时不用再忍受 LaTeX 动辄几分钟的编译和宏包报错，语法像 Markdown 一样简单。",
        "install_cmd": "brew install typst",
        "prompt_recipe": "请把下面这段数学推导和实验分析转换成排版优雅的 Typst (.typ) 代码，包含带编号的公式块、三线表与中文宋体/黑体混排设置。"
    },
    {
        "repo": "Future-House/paper-qa",
        "group": "college",
        "group_label": "🎓 大学工科与课业",
        "badge": "读论文零幻觉问答",
        "title_zh": "PaperQA2 · 专门啃硬核理工科文献的智能科研助手",
        "one_sentence": "做课程综述或进实验室读英文顶会论文时，每句回答都精准标出原文 PDF 页码与数据出处，彻底杜绝 AI 瞎编参考文献。",
        "install_cmd": "pip install paper-qa",
        "prompt_recipe": "请阅读我上传的这几篇论文，用大白话回答：1) 它们各自解决的核心工程瓶颈是什么？2) 实验对比表格里的 baseline 在什么条件下会失效？请标出原文具体段落。"
    },

    # 2. 创业与独立开发
    {
        "repo": "mankidev/antialgorithm",
        "group": "startup",
        "group_label": "🚀 创业与独立开发",
        "badge": "告别塑料 AI 网页感",
        "title_zh": "Antialgorithm · 让你的创业落地页与产品 UI 摆脱「一眼 AI 模板」的审美技能",
        "one_sentence": "做创业 MVP、小程序或路演网页时，强制 AI 跳出千篇一律的紫蓝渐变和圆角卡片，直接做出有独立设计工作室质感的产品界面。",
        "install_cmd": "git clone https://github.com/mankidev/antialgorithm.git",
        "prompt_recipe": "请调用 antialgorithm 技能设计我的创业产品落地页：拒绝廉价毛玻璃和千篇一律的 SaaS 三栏卡片，采用高对比度的纸质编辑部排版与真实的产品交互演示。"
    },
    {
        "repo": "unclecode/crawl4ai",
        "group": "startup",
        "group_label": "🚀 创业与独立开发",
        "badge": "竞品与用户痛点抓取",
        "title_zh": "Crawl4AI · 专为大模型设计的极速网页与竞品评论抓取工具",
        "one_sentence": "创业做市场调研时，3 秒把竞品官网、定价页或社区差评抓成干净的结构化文本，让 AI 直接帮你找出用户还没被满足的痛点。",
        "install_cmd": "pip install crawl4ai",
        "prompt_recipe": "这是我用 Crawl4AI 抓取的 3 家竞品用户评论与功能页。请帮我按「用户抱怨最多的高频痛点」「付费意愿最强的刚需功能」「我们可以切入的差异化卖点」输出一份一页纸创业调研表。"
    },
    {
        "repo": "browser-use/browser-use",
        "group": "startup",
        "group_label": "🚀 创业与独立开发",
        "badge": "AI 自动操作浏览器",
        "title_zh": "Browser-Use · 用一句话让 AI 替你操作浏览器跑完繁琐网页流程",
        "one_sentence": "不用写复杂的爬虫脚本，直接用大白话让 AI 自动打开网页填表、跨平台比价、搜集创业线索或自动测试你的网页产品。",
        "install_cmd": "pip install browser-use",
        "prompt_recipe": "使用 browser-use 自动打开目标网站，检索近一周热门新品榜单，提取前 20 名的标题、价格区间与核心卖点并汇总为 CSV 表格。"
    },

    # 3. 日常生活与个人效率
    {
        "repo": "yt-dlp/yt-dlp",
        "group": "life",
        "group_label": "☕ 日常生活便利",
        "badge": "长视频/网课秒变笔记",
        "title_zh": "yt-dlp + AI 字幕总结 · 2 小时网课或播客 30 秒提炼出核心干货",
        "one_sentence": "遇到超长的 B 站教程、公开课或访谈视频不用倍速硬熬，一行命令只下字幕丢给 AI，半分钟拿走带时间戳的精华笔记。",
        "install_cmd": "brew install yt-dlp",
        "prompt_recipe": "这是我用 `yt-dlp --write-auto-sub --skip-download` 提取的视频字幕。请帮我剔除所有寒暄和废话，按时间轴列出核心观点、实操步骤和金句。"
    },
    {
        "repo": "danielmiessler/fabric",
        "group": "life",
        "group_label": "☕ 日常生活便利",
        "badge": "生活高频提示词百宝箱",
        "title_zh": "Fabric · 社区千锤百炼的数百个生活、阅读与写作提效指令库",
        "one_sentence": "内置现成的租房合同避坑审查、长文脱水、特种兵旅行规划、邮件高情商回复等指令模板，不用每次自己抓耳挠腮想提示词。",
        "install_cmd": "brew install fabric-ai",
        "prompt_recipe": "请扮演严苛的法务与生活管家，逐条审查我即将签署的这份租房/兼职合同：标出所有隐形扣款、押金退还陷阱与不对等违约责任，并给出修改话术。"
    },
    {
        "repo": "immich-app/immich",
        "group": "life",
        "group_label": "☕ 日常生活便利",
        "badge": "自然语言搜板书/照片",
        "title_zh": "Immich · 支持直接用大白话搜「上周拍的高数板书/发票/身份证」的私有相册",
        "one_sentence": "本地跑的智能相册，随手拍的课堂板书、实验接线图、报销发票或旅行照片，直接搜一句话就能秒找出来。",
        "install_cmd": "docker compose up -d",
        "prompt_recipe": "帮我整理相册里所有课堂板书与实验台照片的归档命名规则，按「课程名_日期_核心章节」自动生成整理脚本。"
    },

    # 4. 接地气量化实战（完全对齐你的 31 讲课程进度，不搞看不懂的天书）
    {
        "repo": "akfamily/akshare",
        "group": "quant",
        "group_label": "📈 你的量化课实战助手",
        "badge": "对齐基础课：数据与多因子清洗",
        "title_zh": "AKShare + A 股多因子清洗与 ICIR 检验助手（基础课 1~6 讲实战）",
        "one_sentence": "免费拉取 A 股日线与中证 1000 成分股，一键生成你学过的「剔除涨停/ST/新股 → MAD 去极值 → 行业市值中性化 → ICIR 与五分层回测」标准 Pandas 代码。",
        "install_cmd": "pip install akshare --upgrade",
        "prompt_recipe": "我在学量化，已学完基础课、进阶课和高阶 Part 1（会 Pandas 数据清洗、MAD 去极值、行业市值中性化、ICIR 单因子检验与分层回测）。请用 akshare 拉取中证 1000 成分股数据，帮我实现一个换手率波动率因子的清洗、中性化与 5 分层回测脚本，注意严格规避未来函数。"
    },
    {
        "repo": "dmlc/xgboost",
        "group": "quant",
        "group_label": "📈 你的量化课实战助手",
        "badge": "对齐进阶课：机器学习防未来函数",
        "title_zh": "XGBoost / 随机森林滚动训练与「防未来函数泄漏」审查助手（进阶课 1~6 讲）",
        "one_sentence": "写树模型滚动预测沪深 300 收益、gplearn 挖因子或 HMM/RSRS 择时代码时，专门帮你排查特征标准化和 Target 标签里有没有不小心偷看未来数据。",
        "install_cmd": "pip install xgboost scikit-learn hmmlearn",
        "prompt_recipe": "我已学完量化进阶课（决策树/随机森林/XGBoost 滚动训练、gplearn 遗传规划挖因子、HMM 与 RSRS 择时）。请帮我审查下面这段滚动训练代码是否存在未来函数（如跨期标准化、涨跌停无法买入却计入收益），并给出修正后的滚动窗口训练模板。"
    },
    {
        "repo": "vnpy/vnpy",
        "group": "quant",
        "group_label": "📈 你的量化课实战助手",
        "badge": "对齐待学 Part 2 & 4：事件驱动与实盘拆单",
        "title_zh": "下一步抢先学：公告事件驱动 & miniQMT 实盘拆单白话导学（待学 Part 2 & 4）",
        "one_sentence": "用你已经掌握的因子回测和 Level-2 逐笔订单流作为基础，用大白话和最少代码带你预习接下来要学的「回购/解禁事件驱动」与「TWAP/VWAP 拆单交易」。",
        "install_cmd": "pip install vnpy",
        "prompt_recipe": "我已掌握 A 股多因子回测与 Level-2 逐笔订单流因子，但还没学 Part 2（另类事件驱动、行业轮动、CTA）和 Part 4（miniqmt 实盘与 TWAP/VWAP 拆单）。请从我懂的 Pandas 回测与订单流角度出发，用大白话和一段极简 Python 代码给我讲透：TWAP/VWAP 拆单在代码里到底是怎么根据逐笔成交量切片的？"
    }
]


def src_practical_skills():
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]

    def fetch_seed(seed):
        repo = seed["repo"]
        url = f"https://api.github.com/repos/{repo}"
        stars = None
        pushed_at = iso(NOW)
        try:
            data = http_json(url, headers)
            stars = data.get("stargazers_count")
            pushed_at = iso(parse_time(data.get("pushed_at") or data.get("updated_at")))
        except Exception:
            pass
        entry = dict(seed)
        entry.update({
            "id": make_id(f"https://github.com/{repo}"),
            "url": f"https://github.com/{repo}",
            "stars": stars,
            "pushed_at": pushed_at,
        })
        return entry

    with ThreadPoolExecutor(6) as ex:
        return list(ex.map(fetch_seed, PRACTICAL_SKILLS_SEEDS))


# ----------------------------------------------------------------------------
# 社区来源
# ----------------------------------------------------------------------------
HN_QUERIES = ["LLM", "GPT", "Claude", "Gemini", "DeepSeek", "Qwen", "Kimi", "OpenAI",
              "Anthropic", "AI agent", "MCP", "vibe coding", "local model", "benchmark AI"]
SHOW_HN_QUERIES = ["AI", "LLM", "Claude", "agent", "game", "simulator", "visualizer"]


def src_hackernews():
    hits = {}
    since3 = int((NOW - timedelta(days=3)).timestamp())
    since7 = int((NOW - timedelta(days=7)).timestamp())
    base = "https://hn.algolia.com/api/v1/search?"

    def run(params):
        try:
            return http_json(base + urllib.parse.urlencode(params)).get("hits", [])
        except Exception:
            return []

    jobs = [{"query": q, "tags": "story", "hitsPerPage": 25,
             "numericFilters": f"points>=40,created_at_i>{since3}"} for q in HN_QUERIES]
    jobs += [{"query": q, "tags": "show_hn", "hitsPerPage": 15,
              "numericFilters": f"points>=12,created_at_i>{since7}"} for q in SHOW_HN_QUERIES]
    with ThreadPoolExecutor(8) as ex:
        for result in ex.map(run, jobs):
            for h in result:
                hits[h["objectID"]] = h
    if not hits:
        raise RuntimeError("Algolia 无返回")

    top = sorted(hits.values(), key=lambda h: h.get("points") or 0, reverse=True)[:45]

    def comments_of(h):
        try:
            data = http_json(f"https://hn.algolia.com/api/v1/items/{h['objectID']}")
            texts = [clean(c.get("text"), 260) for c in data.get("children", []) if c.get("text")]
            return texts[:3]
        except Exception:
            return []

    with ThreadPoolExecutor(8) as ex:
        all_comments = list(ex.map(comments_of, top[:30])) + [[]] * max(0, len(top) - 30)

    out = []
    for h, cm in zip(top, all_comments):
        discuss = f"https://news.ycombinator.com/item?id={h['objectID']}"
        out.append(item(
            source="hn", source_label="Hacker News" + (" · Show HN" if "show_hn" in h.get("_tags", []) else ""),
            title=h.get("title") or "", url=h.get("url") or discuss, discuss_url=discuss,
            published_at=iso(parse_time(h.get("created_at"))),
            points=h.get("points"), comments=h.get("num_comments"),
            snippet=clean(h.get("story_text"), 300),
            community_comments=cm,
        ))
    return out


def src_lobsters():
    out = []
    for s in http_json("https://lobste.rs/t/ai.json"):
        dt = parse_time(s.get("created_at"))
        if not recent(dt, 7):
            continue
        out.append(item(
            source="lobsters", source_label="Lobsters", title=s.get("title", ""),
            url=s.get("url") or s.get("comments_url"), discuss_url=s.get("comments_url"),
            published_at=iso(dt), points=s.get("score"), comments=s.get("comment_count"),
            snippet=clean(s.get("description_plain"), 300),
        ))
    return out


def src_simonwillison():
    root = ET.fromstring(http("https://simonwillison.net/atom/everything/"))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for e in root.findall("a:entry", ns):
        dt = parse_time(e.findtext("a:published", "", ns) or e.findtext("a:updated", "", ns))
        if not recent(dt, 7):
            continue
        link = e.find("a:link", ns)
        url = link.attrib.get("href") if link is not None else ""
        body = e.findtext("a:summary", "", ns) or e.findtext("a:content", "", ns)
        out.append(item(
            source="simon", source_label="Simon Willison", title=clean(e.findtext("a:title", "", ns), 200),
            url=url, published_at=iso(dt), snippet=clean(body, 600),
        ))
    return out


def src_github():
    since = (NOW - timedelta(days=14)).strftime("%Y-%m-%d")
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    repos = {}
    for topic in ["llm", "ai-agent", "agents", "generative-ai", "mcp"]:
        q = f"topic:{topic} created:>{since} stars:>=150"
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
            {"q": q, "sort": "stars", "order": "desc", "per_page": 10})
        for r in http_json(url, headers).get("items", []):
            repos[r["full_name"]] = r
    out = []
    for r in sorted(repos.values(), key=lambda r: r["stargazers_count"], reverse=True)[:18]:
        out.append(item(
            source="github", source_label="GitHub 新仓库", title=r["full_name"], url=r["html_url"],
            published_at=iso(parse_time(r["created_at"])), points=r["stargazers_count"],
            snippet=clean(r.get("description"), 300) + f" | topics: {', '.join(r.get('topics', [])[:6])}",
            points_label="stars",
        ))
    return out


def src_hf_spaces():
    out = []
    for s in http_json("https://huggingface.co/api/spaces?sort=trendingScore&limit=20&full=true"):
        card = s.get("cardData") or {}
        out.append(item(
            source="hf_space", source_label="Hugging Face Space",
            title=card.get("title") or s["id"], url=f"https://huggingface.co/spaces/{s['id']}",
            published_at=iso(parse_time(s.get("lastModified") or s.get("createdAt"))),
            points=s.get("likes"), points_label="likes",
            snippet=clean(card.get("short_description") or "", 200) + f" | id: {s['id']}",
            playable=True,
        ))
    return out


V2EX_NODES = ["openai", "claude", "gemini", "deepseek", "llm", "localllm"]


def src_v2ex():
    out = []
    for node in V2EX_NODES:
        try:
            topics = http_json(f"https://www.v2ex.com/api/topics/show.json?node_name={node}")
        except Exception:
            continue
        for t in topics if isinstance(topics, list) else []:
            dt = parse_time(t.get("created"))
            if not recent(dt, 4) or (t.get("replies") or 0) < 8:
                continue
            out.append(item(
                source="v2ex", source_label=f"V2EX · {node}", title=t.get("title", ""), url=t["url"],
                discuss_url=t["url"], published_at=iso(dt), comments=t.get("replies"),
                snippet=clean(t.get("content"), 300),
            ))
    if not out:
        raise RuntimeError("近 4 天无高回复帖")
    return out


# ----------------------------------------------------------------------------
# 官方来源
# ----------------------------------------------------------------------------
def rss_items(url, org, region, days=14, limit=25):
    root = ET.fromstring(http(url))
    out = []
    for it in list(root.iter("item"))[:limit]:
        dt = parse_time(it.findtext("pubDate"))
        if not recent(dt, days):
            continue
        out.append(item(
            source="official", org=org, region=region, title=clean(it.findtext("title"), 200),
            url=(it.findtext("link") or "").strip(), published_at=iso(dt),
            snippet=clean(it.findtext("description"), 300), kind="post",
        ))
    return out


def src_openai():
    return rss_items("https://openai.com/news/rss.xml", "OpenAI", "US")


def src_google():
    return rss_items("https://blog.google/technology/ai/rss/", "Google", "US") + \
        rss_items("https://deepmind.google/blog/rss.xml", "Google DeepMind", "US")


MONTHS = "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"


def src_anthropic():
    page = http("https://www.anthropic.com/news", {"User-Agent": "Mozilla/5.0 " + UA})
    out, seen = [], set()
    for row in page.split("data-listing-row=")[1:]:
        row = row[:6000]
        link_m = re.search(r'href="([^"#]+)"[^>]*>(?:(?!</a>).)*?<h[1-6]', row, re.S)
        date_m = re.search(rf"<time[^>]*>\s*((?:{MONTHS})[a-z]*\.? \d{{1,2}}, 20\d\d)\s*</time>", row)
        head_m = re.search(r"<h[1-6][^>]*>(.*?)</h[1-6]>", row, re.S)
        if not (link_m and date_m and head_m):
            continue
        path, title = link_m.group(1), clean(head_m.group(1), 200)
        if path in seen:
            continue
        para = re.search(r"<p[^>]*>(.*?)</p>", row, re.S)
        inner = para.group(1) if para else ""
        try:
            dt = datetime.strptime(date_m.group(1).replace(".", ""), "%b %d, %Y")
        except ValueError:
            dt = datetime.strptime(date_m.group(1), "%B %d, %Y")
        dt = dt.replace(tzinfo=timezone.utc)
        if not title or not recent(dt, OFFICIAL_KEEP_DAYS):
            continue
        seen.add(path)
        out.append(item(
            source="official", org="Anthropic", region="US", title=title,
            url=urllib.parse.urljoin("https://www.anthropic.com/news", path), published_at=iso(dt),
            snippet=clean(inner, 300), kind="post",
        ))
    if not out:
        raise RuntimeError("页面结构变化，未解析到带日期的文章")
    return out


HF_ORGS = {
    "deepseek-ai": ("DeepSeek", "CN"), "Qwen": ("通义千问 Qwen", "CN"), "moonshotai": ("月之暗面 Kimi", "CN"),
    "zai-org": ("智谱 Z.ai", "CN"), "MiniMaxAI": ("MiniMax", "CN"), "stepfun-ai": ("阶跃星辰", "CN"),
    "tencent": ("腾讯混元", "CN"), "baidu": ("百度", "CN"), "XiaomiMiMo": ("小米 MiMo", "CN"),
    "ByteDance-Seed": ("字节 Seed", "CN"), "inclusionAI": ("蚂蚁 inclusionAI", "CN"),
    "openai": ("OpenAI", "US"), "google": ("Google", "US"), "meta-llama": ("Meta", "US"),
    "mistralai": ("Mistral", "EU"),
}
QUANT_PAT = re.compile(r"(gguf|awq|gptq|fp8|int4|int8|mlx|bnb|-\d+bit|quant)", re.I)


def src_hf_releases():
    def org_models(org):
        try:
            return org, http_json(f"https://huggingface.co/api/models?author={org}&sort=createdAt&direction=-1&limit=20")
        except Exception:
            return org, []

    out = []
    with ThreadPoolExecutor(6) as ex:
        for org, models in ex.map(org_models, HF_ORGS):
            name, region = HF_ORGS[org]
            fresh = [m for m in models if recent(parse_time(m.get("createdAt")), OFFICIAL_KEEP_DAYS)
                     and not QUANT_PAT.search(m["id"])]
            fresh.sort(key=lambda m: m.get("likes") or 0, reverse=True)
            for m in fresh[:2]:
                out.append(item(
                    source="official", org=name, region=region, kind="release",
                    title=f"{m['id'].split('/')[-1]}", url=f"https://huggingface.co/{m['id']}",
                    published_at=iso(parse_time(m.get("createdAt"))), points=m.get("likes"),
                    snippet=f"Hugging Face 新模型 · {m.get('pipeline_tag') or ''} · 下载 {m.get('downloads', 0)}",
                ))
    return out


def src_hf_trending_models():
    out = []
    for m in http_json("https://huggingface.co/api/models?sort=trendingScore&limit=12"):
        out.append({"id": m["id"], "url": f"https://huggingface.co/{m['id']}", "likes": m.get("likes"),
                    "downloads": m.get("downloads"), "task": m.get("pipeline_tag")})
    return out


COMMUNITY_SOURCES = [
    ("Hacker News", src_hackernews), ("Simon Willison", src_simonwillison), ("Lobsters", src_lobsters),
    ("GitHub 新仓库", src_github), ("Hugging Face Spaces", src_hf_spaces), ("V2EX", src_v2ex),
]
OFFICIAL_SOURCES = [
    ("OpenAI 官方", src_openai), ("Google / DeepMind 官方", src_google), ("Anthropic 官方", src_anthropic),
    ("Hugging Face 厂商发布", src_hf_releases),
]
SKILL_SOURCES = [
    ("实用 Skill 宝库", src_practical_skills),
]
UNAVAILABLE = [
    ("Reddit", "Reddit 拒绝未登录的程序访问（403/429），暂不抓取"),
    ("Linux.do", "站点开启了反爬验证（403），暂不抓取"),
]


def run_sources(sources):
    results, status = [], []

    def run(entry):
        name, fn = entry
        try:
            items = fn()
            return name, items, None
        except Exception as e:
            return name, [], f"{type(e).__name__}: {e}"[:160]

    with ThreadPoolExecutor(len(sources)) as ex:
        for name, items, err in ex.map(run, sources):
            results.extend(items)
            status.append({"name": name, "ok": err is None, "count": len(items), "error": err})
            print(f"  {'✓' if err is None else '✗'} {name}: {len(items)} 条" + (f"  ({err})" if err else ""))
    return results, status


# ----------------------------------------------------------------------------
# DeepSeek 提纯（强制一句话讲清价值，绝不啰嗦）
# ----------------------------------------------------------------------------
def deepseek_json(key, system, user, model=DIGEST_MODEL, timeout=240):
    for attempt in range(3):
        payload = json.dumps({
            "model": model,
            "reasoning_effort": "low",
            "response_format": {"type": "json_object"},
            "temperature": 0.2 if attempt else 0.35,
            "max_tokens": 16384,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }).encode()
        raw = http("https://api.deepseek.com/chat/completions",
                   {"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
                   data=payload, timeout=timeout)
        content = json.loads(raw)["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.S)
        try:
            return json.loads(content)
        except Exception as e:
            if attempt == 2:
                raise e


COMMUNITY_SYSTEM = """你是「野生 AI 雷达」的主编。读者是一位喜欢玩 AI、学工科的大学生。
他讨厌冗长难懂的黑话，要求每一条社群资讯都必须【用大白话一句话讲清楚价值在哪、好玩在哪或能解决什么问题】。

你会收到一组编号条目（来自 Hacker News、Simon Willison 博客、Lobsters、GitHub、Hugging Face、V2EX）。

硬性规则：
1. 只能从给定条目中挑选，用 ref 编号引用。绝不编造任何事实、链接、数字。
2. 强力去同质化：同一件事只留热度最高的一条；剔除无聊的公关软文、招聘、纯股价新闻。
3. 选 14~20 条，优先选「好玩的可视化/可玩项目」和「能提效的新工具/野生实测」。
4. category 只能是：
   - "play"  好玩的作品、游戏、可视化实验、可在线试玩的 Demo
   - "tool"  能省时间的新开源工具、实用小项目
   - "bench" 野生评测 / 模型实测对比
   - "talk"  有干货的社区热议话题
5. title_zh：干净利落的中文标题，不超过 28 个字。
6. why：【必须只有一句话，不超过 55 个字！】直接讲明白「它到底能干嘛 / 价值或好玩在哪」，严禁堆砌术语。
7. prompt：只有当片段里真出现了可复用提示词时才摘录，否则为 null。
8. tags：2 个简短中文标签。
9. fun：1~5，代表好玩或实用程度。

只输出合法 JSON（中文内部如需引号一律用「」）：
{"briefing":{"headline":"一句话概括本周最好玩的 AI 趋势（不超过 26 字）","points":[{"text":"一句话趋势看点（不超过 42 字）","refs":[1,2]}]},
 "picks":[{"ref":1,"category":"play","title_zh":"...","why":"一句话讲清价值或好玩在哪（<=55字）","prompt":null,"tags":["..."],"fun":5}]}"""

OFFICIAL_SYSTEM = """你是「野生 AI 雷达」的编辑，负责整理 AI 大厂大事记。
硬性规则：
1. 只依据给定文本，不编造信息。
2. title_zh：简洁明了的中文标题，不超过 26 字。
3. summary_zh：【必须只有一句话，不超过 45 个字！】直接讲清楚「这项发布对普通人或开发者有什么实际用处/价值」。
4. importance：3=新模型/新功能重磅发布；2=有价值的技术更新；1=无聊公关稿/客户案例（importance=1 会被自动丢弃）。
只输出 JSON：{"items":[{"ref":1,"title_zh":"...","summary_zh":"一句话讲清价值（<=45字）","importance":3}]}"""


def digest_community(key, raw):
    lines = []
    for i, r in enumerate(raw):
        entry = {"ref": i, "source": r["source_label"], "title": r["title"], "snippet": r.get("snippet", "")[:320]}
        if r.get("points") is not None:
            entry["points"] = r["points"]
        if r.get("comments") is not None:
            entry["comments"] = r["comments"]
        if r.get("community_comments"):
            entry["top_comments"] = r["community_comments"]
        lines.append(entry)
    return deepseek_json(key, COMMUNITY_SYSTEM, json.dumps(lines, ensure_ascii=False))


def digest_official(key, raw):
    lines = [{"ref": i, "org": r["org"], "title": r["title"], "snippet": r.get("snippet", "")[:280]}
             for i, r in enumerate(raw)]
    return deepseek_json(key, OFFICIAL_SYSTEM, json.dumps(lines, ensure_ascii=False))


PUBLIC_FIELDS = ["id", "source", "source_label", "title", "url", "discuss_url", "published_at",
                 "points", "points_label", "comments", "playable"]


def load_previous():
    if os.path.exists(FEED_JSON):
        try:
            return json.load(open(FEED_JSON, encoding="utf-8"))
        except Exception:
            pass
    return {}


def merge(new_items, old_items, keep_days, limit, sort_key):
    old = {o["id"]: o for o in old_items or [] if "id" in o and o.get("title_zh")}
    merged = {}
    for n in new_items:
        prev = old.get(n["id"])
        if prev:
            n["first_seen"] = prev.get("first_seen", n["first_seen"])
        merged[n["id"]] = n
    for oid, o in old.items():
        if oid not in merged and recent(parse_time(o.get("first_seen") or o.get("published_at")), keep_days):
            merged[oid] = o
    return sorted(merged.values(), key=sort_key, reverse=True)[:limit]


def build_community(key, raw):
    picks, briefing = [], None
    if key and raw:
        try:
            result = digest_community(key, raw)
            picks = result.get("picks", [])
            briefing = result.get("briefing")
        except Exception as e:
            print(f"  ✗ DeepSeek 社区提纯失败: {e}")
    if not picks:
        ranked = sorted(range(len(raw)), key=lambda i: raw[i].get("points") or raw[i].get("comments") or 0, reverse=True)
        picks = [{"ref": i, "category": "talk", "title_zh": None, "why": raw[i].get("snippet") or "",
                  "prompt": None, "tags": [], "fun": 0} for i in ranked[:18]]

    out = []
    for rank, p in enumerate(picks):
        ref = p.get("ref")
        if not isinstance(ref, int) or not 0 <= ref < len(raw):
            continue
        r = raw[ref]
        entry = {k: r.get(k) for k in PUBLIC_FIELDS}
        entry.update({
            "title_zh": p.get("title_zh"), "why": p.get("why"),
            "category": p.get("category") if p.get("category") in ("play", "bench", "tool", "talk") else "talk",
            "prompt": p.get("prompt") or None, "tags": (p.get("tags") or [])[:2],
            "fun": p.get("fun") or 0, "rank": rank, "first_seen": iso(NOW),
            "week_label": WEEK_LABEL,
        })
        out.append(entry)

    if briefing:
        for pt in briefing.get("points", []):
            pt["ids"] = [raw[i]["id"] for i in pt.pop("refs", []) if isinstance(i, int) and 0 <= i < len(raw)]
        briefing["generated_at"] = iso(NOW)
    return out, briefing


def build_official(key, raw):
    posts = [r for r in raw if r.get("kind") == "post"]
    releases = [r for r in raw if r.get("kind") == "release"]
    result = {}
    if key and posts:
        try:
            result = {x["ref"]: x for x in digest_official(key, posts).get("items", []) if isinstance(x.get("ref"), int)}
        except Exception as e:
            print(f"  ✗ DeepSeek 官方动态整理失败: {e}")
    out = []
    for i, r in enumerate(posts):
        d = result.get(i, {})
        if d.get("importance", 2) <= 1:
            continue
        out.append({"id": r["id"], "org": r["org"], "region": r["region"], "kind": "post",
                    "title": r["title"], "title_zh": d.get("title_zh"), "summary_zh": d.get("summary_zh"),
                    "importance": d.get("importance", 2), "url": r["url"], "published_at": r["published_at"],
                    "first_seen": iso(NOW)})
    for r in releases:
        out.append({"id": r["id"], "org": r["org"], "region": r["region"], "kind": "release",
                    "title": r["title"], "title_zh": f"{r['org']} 开源发布 {r['title']} 模型权重",
                    "summary_zh": f"可直接下载部署的官方新模型权重（{r['snippet']}）。", "importance": 2, "likes": r.get("points"),
                    "url": r["url"], "published_at": r["published_at"], "first_seen": iso(NOW)})
    return out


def load_classics_with_inline_html():
    """
    把每个实盘 Demo 的 HTML 源码直接内联打包进 classics 数据结构，
    这样前端无论用 srcdoc 还是 Blob 全屏打开都 100% 零网络依赖，永远不会出现 'not connected'！
    """
    if not os.path.exists(CLASSICS_JSON):
        return []
    classics = json.load(open(CLASSICS_JSON, encoding="utf-8"))
    for c in classics:
        for r in c.get("runs", []):
            rel = r.get("file", "")
            full = os.path.join(ROOT, rel)
            if rel and os.path.exists(full):
                r["inline_html"] = open(full, encoding="utf-8").read()
    return classics


def write_feed(feed):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FEED_JSON, "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False, indent=1)
    classics = load_classics_with_inline_html()
    bundle = dict(feed, classics=classics)
    with open(FEED_JS, "w", encoding="utf-8") as f:
        f.write("// 自动生成，请勿手改。内联包含实盘 HTML 源码以确保离线/全屏 100% 可用\n")
        f.write("window.RADAR = " + json.dumps(bundle, ensure_ascii=False) + ";\n")


def main():
    use_llm = "--no-llm" not in sys.argv
    key = load_key() if use_llm else ""
    print(f"📡 野生 AI 雷达开始抓取 · {iso(NOW)} ({WEEK_LABEL}) · 模型: {DIGEST_MODEL if key else '不使用'}")

    print("实用 Skill 宝库：")
    skills, skill_status = run_sources(SKILL_SOURCES)
    print("社区来源：")
    community_raw, community_status = run_sources(COMMUNITY_SOURCES)
    print("官方来源：")
    official_raw, official_status = run_sources(OFFICIAL_SOURCES)
    try:
        hf_trending = src_hf_trending_models()
    except Exception:
        hf_trending = []

    dedup = {}
    for r in community_raw:
        if r["id"] not in dedup or (r.get("points") or 0) > (dedup[r["id"]].get("points") or 0):
            dedup[r["id"]] = r
    community_raw = list(dedup.values())

    prev = load_previous()
    community, briefing = build_community(key, community_raw)
    official = build_official(key, official_raw)

    feed = {
        "schema": 4,
        "week_label": WEEK_LABEL,
        "generated_at": iso(NOW),
        "model": DIGEST_MODEL if key else None,
        "skills": skills or prev.get("skills", []),
        "briefing": briefing or prev.get("briefing"),
        "community": merge(community, prev.get("community"), COMMUNITY_KEEP_DAYS, COMMUNITY_MAX,
                           lambda x: (x.get("first_seen", "")[:10], -(x.get("rank") or 0))),
        "official": merge(official, prev.get("official"), OFFICIAL_KEEP_DAYS, OFFICIAL_MAX,
                          lambda x: x.get("published_at", "")),
        "hf_trending": hf_trending or prev.get("hf_trending", []),
        "sources": skill_status + community_status + official_status,
        "unavailable": [{"name": n, "reason": r} for n, r in UNAVAILABLE],
    }
    write_feed(feed)
    print(f"💾 完成：实用 Skills {len(feed['skills'])} 条，社区 {len(feed['community'])} 条，官方 {len(feed['official'])} 条")


if __name__ == "__main__":
    main()
