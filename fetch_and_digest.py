#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 雷达 · 抓取 + DeepSeek 提纯
================================
用法：
    python3 fetch_and_digest.py            # 抓取全部来源并用 DeepSeek 提纯（需要 DEEPSEEK_API_KEY）
    python3 fetch_and_digest.py --no-llm   # 只抓取，不调用模型（摘要退化为原文片段）

设计原则（改动前请读 AI_GUIDE.md）：
1. 一切链接、日期、热度数字都来自原始数据源，模型只能用 ref 编号引用条目，不能生成链接或数字。
2. 某个来源失败不影响其他来源；失败会如实写入 feed.sources，页面上能看到。
3. 只用 Python 标准库，GitHub Actions 里不需要 pip install。
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

UA = "ai-radar/2.0 (+https://github.com/sxy3481841323-ship-it/ai-pulse-radar)"
NOW = datetime.now(timezone.utc)
DIGEST_MODEL = os.environ.get("RADAR_MODEL", "deepseek-flash")
COMMUNITY_KEEP_DAYS = 10
COMMUNITY_MAX = 90
OFFICIAL_KEEP_DAYS = 30
OFFICIAL_MAX = 40
SSL_CTX = ssl.create_default_context()


# ----------------------------------------------------------------------------
# 基础工具
# ----------------------------------------------------------------------------
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
# 社区来源
# ----------------------------------------------------------------------------
HN_QUERIES = ["LLM", "GPT", "Claude", "Gemini", "DeepSeek", "Qwen", "Kimi", "OpenAI",
              "Anthropic", "AI agent", "AI model", "vibe coding", "local model", "benchmark AI"]
SHOW_HN_QUERIES = ["AI", "LLM", "GPT", "Claude", "agent", "model"]


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
            source="hf_space", source_label="Hugging Face Space（可在线试玩）",
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
    # 新闻列表每一行是 <li data-listing-row=...>，里面有 <h3> 标题、/news/ 链接和 <time> 日期
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
# DeepSeek
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


COMMUNITY_SYSTEM = """你是「AI 雷达」的编辑。读者是一位想绕开自媒体二手消息、直接看一手 AI 社区的中文用户。
他最想看的是：社区里的整活、野生评测（类似"鹈鹕骑自行车"那种民间测试）、好玩的小项目；其次是社区在热议的话题。

你会收到一组编号条目（来自 Hacker News、Simon Willison 博客、Lobsters、GitHub、Hugging Face、V2EX），包含标题、片段、热度和部分社区评论。

硬性规则：
1. 只能从给定条目中挑选，用 ref 编号引用。绝不编造任何事实、链接、数字、人名。
2. 只选与 AI / 大模型直接相关的条目。剔除：广告营销、招聘、单纯融资或股价新闻、疑似刷星的仓库、与 AI 无关的内容、重复话题（同一件事只留热度最高的一条）。
3. 选 14~22 条，按「有趣程度 × 社区热度」从高到低排序。
4. category 只能是：
   - "play"  整活 / 好玩的作品、游戏、创意实验
   - "bench" 野生评测 / 模型对比 / 社区自发的测试与实测
   - "tool"  新开源项目、新工具、可以上手的 Demo
   - "talk"  热议话题、观点、争议、行业讨论
5. title_zh：忠实原意的中文标题，口语化但不标题党，不超过 32 个字。
6. why：2~3 句大白话，说清「这是什么」「社区为什么在关注 / 好玩在哪」，如果给了评论，再用一句话概括评论区的主流看法。只依据提供的文本；信息不够就直说"原帖信息有限"。不超过 120 个字。
7. prompt：只有当片段或评论里出现了可以直接复用的提示词原文时才原样摘录，否则必须为 null。
8. tags：2~3 个中文短标签。
9. fun：1~5，越好玩越高。

另外写一份今日简报 briefing：
- headline：一句话概括社区这两天最关注什么（不超过 28 字）。
- points：3~5 条，每条不超过 55 字，讲一个趋势或话题，并在 refs 里列出支撑它的条目编号。

只输出合法 JSON（注意：中文文本内部如需引号请一律使用中文引号「」或『』，严禁在 JSON 字符串值内部出现未转义的英文双引号 "）：
{"briefing":{"headline":"...","points":[{"text":"...","refs":[1,2]}]},
 "picks":[{"ref":1,"category":"play","title_zh":"...","why":"...","prompt":null,"tags":["..."],"fun":4}]}"""

OFFICIAL_SYSTEM = """你是「AI 雷达」的编辑，负责整理 AI 公司官方发布。你会收到一组编号条目（官方博客文章或 Hugging Face 新模型）。
规则：
1. 只依据给定文本，不编造任何信息。
2. title_zh：准确的中文标题，不超过 30 字。模型名、产品名保留英文原文。
3. summary_zh：一句话说明这条发布是什么、对开发者或普通用户意味着什么，不超过 60 字；信息不够就只描述是什么。
4. importance：3=新模型/新产品/重大能力或政策变化；2=有价值的研究、功能更新；1=客户案例、营销活动、招聘、人物访谈、泛泛的观点文章。
只输出 JSON：{"items":[{"ref":1,"title_zh":"...","summary_zh":"...","importance":3}]}"""


def digest_community(key, raw):
    lines = []
    for i, r in enumerate(raw):
        entry = {"ref": i, "source": r["source_label"], "title": r["title"], "snippet": r.get("snippet", "")[:350]}
        if r.get("points") is not None:
            entry["points"] = r["points"]
        if r.get("comments") is not None:
            entry["comments"] = r["comments"]
        if r.get("community_comments"):
            entry["top_comments"] = r["community_comments"]
        lines.append(entry)
    return deepseek_json(key, COMMUNITY_SYSTEM, json.dumps(lines, ensure_ascii=False))


def digest_official(key, raw):
    lines = [{"ref": i, "org": r["org"], "title": r["title"], "snippet": r.get("snippet", "")[:300]}
             for i, r in enumerate(raw)]
    return deepseek_json(key, OFFICIAL_SYSTEM, json.dumps(lines, ensure_ascii=False))


# ----------------------------------------------------------------------------
# 合并与输出
# ----------------------------------------------------------------------------
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
    if not picks:  # 无 key 或失败：按热度退化
        ranked = sorted(range(len(raw)), key=lambda i: raw[i].get("points") or raw[i].get("comments") or 0, reverse=True)
        picks = [{"ref": i, "category": "talk", "title_zh": None, "why": raw[i].get("snippet") or "",
                  "prompt": None, "tags": [], "fun": 0} for i in ranked[:20]]

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
            "prompt": p.get("prompt") or None, "tags": (p.get("tags") or [])[:3],
            "fun": p.get("fun") or 0, "rank": rank, "first_seen": iso(NOW),
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
                    "title": r["title"], "title_zh": f"{r['org']} 在 Hugging Face 发布 {r['title']}",
                    "summary_zh": r["snippet"], "importance": 2, "likes": r.get("points"),
                    "url": r["url"], "published_at": r["published_at"], "first_seen": iso(NOW)})
    return out


def write_feed(feed):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FEED_JSON, "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False, indent=1)
    classics = json.load(open(CLASSICS_JSON, encoding="utf-8")) if os.path.exists(CLASSICS_JSON) else []
    bundle = dict(feed, classics=classics)
    with open(FEED_JS, "w", encoding="utf-8") as f:
        f.write("// 自动生成，请勿手改。数据来源见 fetch_and_digest.py，结构说明见 AI_GUIDE.md\n")
        f.write("window.RADAR = " + json.dumps(bundle, ensure_ascii=False) + ";\n")


def main():
    use_llm = "--no-llm" not in sys.argv
    key = load_key() if use_llm else ""
    print(f"📡 AI 雷达开始抓取 · {iso(NOW)} · 模型: {DIGEST_MODEL if key else '不使用'}")

    print("社区来源：")
    community_raw, community_status = run_sources(COMMUNITY_SOURCES)
    print("官方来源：")
    official_raw, official_status = run_sources(OFFICIAL_SOURCES)
    try:
        hf_trending = src_hf_trending_models()
    except Exception:
        hf_trending = []

    # 去重（同一链接被多个来源收录时保留热度更高的）
    dedup = {}
    for r in community_raw:
        if r["id"] not in dedup or (r.get("points") or 0) > (dedup[r["id"]].get("points") or 0):
            dedup[r["id"]] = r
    community_raw = list(dedup.values())

    prev = load_previous()
    community, briefing = build_community(key, community_raw)
    official = build_official(key, official_raw)

    feed = {
        "schema": 2,
        "generated_at": iso(NOW),
        "model": DIGEST_MODEL if key else None,
        "briefing": briefing or prev.get("briefing"),
        "community": merge(community, prev.get("community"), COMMUNITY_KEEP_DAYS, COMMUNITY_MAX,
                           lambda x: (x.get("first_seen", "")[:10], -(x.get("rank") or 0))),
        "official": merge(official, prev.get("official"), OFFICIAL_KEEP_DAYS, OFFICIAL_MAX,
                          lambda x: x.get("published_at", "")),
        "hf_trending": hf_trending or prev.get("hf_trending", []),
        "sources": community_status + official_status,
        "unavailable": [{"name": n, "reason": r} for n, r in UNAVAILABLE],
    }
    write_feed(feed)
    print(f"💾 完成：社区 {len(feed['community'])} 条（本次新增 {len(community)}），官方 {len(feed['official'])} 条")


if __name__ == "__main__":
    main()
