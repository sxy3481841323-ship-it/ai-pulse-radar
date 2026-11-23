#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 极客雷达 (AI Pulse Radar) - 一手社区采集与 DeepSeek 自动提纯引擎
==================================================================
功能：
1. 免 Key 自动并发抓取全球最硬核的一手 AI 极客社区：
   - Simon Willison's Blog (鹈鹕骑自行车测试发源地 Atom Feed)
   - Hacker News (Show HN / AI 热门野生项目 API)
   - Reddit r/LocalLLaMA & r/ClaudeAI & r/Singularity (热门 Showcase JSON/RSS)
2. 调用 DeepSeek API (deepseek-chat) 进行“极客猎手级”过滤与中文提纯：
   - 剔除水帖与普通问答，优先保留「野生基准测试 (如鹈鹕/小鹿骑车)」「单段 Prompt 3A/小游戏」「离谱整活」「头部大厂硬核发布」
   - 自动提炼出【一句话看点 TL;DR】+【复现秘籍 Prompt】+【一手原帖/Demo 链接】
3. 自动同步写入 data/feed.js 与 data/feed.json，前端直接刷新即可浏览。
"""

import json
import os
import re
import ssl
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_JS_PATH = os.path.join(BASE_DIR, "data", "feed.js")
DATA_JSON_PATH = os.path.join(BASE_DIR, "data", "feed.json")
ENV_PATH = os.path.join(BASE_DIR, ".env")


def load_env_key() -> str:
    """从环境变量或本地 .env 文件安全读取 DEEPSEEK_API_KEY"""
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("DEEPSEEK_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def http_get(url: str, timeout: int = 12) -> str:
    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) GeekPulseRadar/1.0"
        },
    )
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_simon_willison(limit: int = 6) -> list:
    """抓取 Simon Willison 博客最新一手文章（鹈鹕骑车等野生评测发源地）"""
    items = []
    try:
        xml_text = http_get("https://simonwillison.net/atom/everything/")
        root = ET.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns)[:limit]:
            title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
            link_el = entry.find("atom:link", ns)
            link = link_el.attrib.get("href", "") if link_el is not None else ""
            summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "")
            summary_clean = re.sub(r"<[^>]+>", " ", summary).strip()[:500]
            items.append({
                "source": "Simon Willison's Blog",
                "title": title,
                "url": link,
                "snippet": summary_clean,
            })
    except Exception as e:
        print(f"[WARN] Simon Willison 抓取跳过: {e}")
    return items


def fetch_hacker_news_ai(limit: int = 8) -> list:
    """通过 Algolia HN API 抓取最新高赞 Show HN AI 野生小项目与评测"""
    items = []
    try:
        url = "https://hn.algolia.com/api/v1/search_by_date?query=LLM%20OR%20Claude%20OR%20DeepSeek%20OR%20benchmark%20OR%20Three.js&tags=story&numericFilters=points>25&hitsPerPage=" + str(limit)
        raw = http_get(url)
        data = json.loads(raw)
        for hit in data.get("hits", [])[:limit]:
            items.append({
                "source": "Hacker News",
                "title": hit.get("title", ""),
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                "snippet": f"Points: {hit.get('points', 0)} | Comments: {hit.get('num_comments', 0)} | Author: {hit.get('author', '')}",
            })
    except Exception as e:
        print(f"[WARN] Hacker News 抓取跳过: {e}")
    return items


def fetch_reddit_feeds(limit_per_sub: int = 5) -> list:
    """抓取 Reddit r/LocalLLaMA 和 r/ClaudeAI 高热一手帖"""
    items = []
    subs = ["LocalLLaMA", "ClaudeAI", "singularity"]
    for sub in subs:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit_per_sub}"
            raw = http_get(url)
            data = json.loads(raw)
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                if post.get("stickied"):
                    continue
                items.append({
                    "source": f"Reddit r/{sub}",
                    "title": post.get("title", ""),
                    "url": "https://www.reddit.com" + post.get("permalink", ""),
                    "snippet": (post.get("selftext", "") or "")[:450],
                })
        except Exception as e:
            print(f"[WARN] Reddit r/{sub} 抓取跳过: {e}")
    return items


def call_deepseek_digest(api_key: str, raw_items: list) -> dict:
    """调用 DeepSeek API 过滤并提纯成极客看板卡片和大厂大事记"""
    system_prompt = """你是一个常年混迹于 Reddit r/LocalLLaMA、Simon Willison 博客、Hacker News 和 GitHub 的硬核 AI 极客猎手。
请从输入的一手英文社区帖子列表中，挑选最有意思、最能反映 AI 真实水位或社区脑洞的 4~6 个野生项目/评测，以及 2~4 条大厂/开源模型硬核动态。

输出严格的 JSON 对象，包含两个数组：
1. "new_projects": 数组，每项包含：
   - "id": 唯一英文短横线ID
   - "title": 吸引人的极客中文标题
   - "category": 只能是 "benchmark" | "game" | "fun" | "tool" 之一
   - "category_label": 对应 "#野生基准测试" | "#一镜到底/3A小游戏" | "#极客整活" | "#开源神仙小玩具"
   - "source_name": 来源社区名
   - "source_url": 原帖链接
   - "demo_url": 原帖或试玩链接
   - "published_at": "今日一手实时抓取"
   - "heat_score": 例如 "🔥 社区高赞实测"
   - "model_tested": 涉及的模型名称
   - "tldr": 用接地气、有洞察力的中文讲清楚这个项目好玩在哪、测出了什么真实水位（80~140字）
   - "prompt_recipe": 提炼或还原出玩家可以用来复现该测试的 Prompt 指令或玩法秘籍
   - "tags": 3~4个中文短标签数组
2. "new_timeline": 数组，每项包含：
   - "id": 唯一英文ID
   - "company": 涉及的公司或开源组织 (如 OpenAI / Anthropic / Google / DeepSeek / Qwen / Meta)
   - "region": "US" 或 "CN"
   - "badge_color": 十六进制亮色 (如 "#38bdf8", "#fb923c", "#4ade80", "#c084fc")
   - "date": "最新动态"
   - "title": 中文简明大事记标题
   - "summary": 一句话讲透对开发者和玩家的核心影响
   - "url": 相关链接
"""

    payload = json.dumps({
        "model": "deepseek-chat",
        "response_format": {"type": "json_object"},
        "temperature": 0.6,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(raw_items, ensure_ascii=False)},
        ],
    }).encode("utf-8")

    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=45, context=ctx) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        content = result["choices"][0]["message"]["content"]
        return json.loads(content)


def load_existing_feed() -> dict:
    if os.path.exists(DATA_JSON_PATH):
        with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    if os.path.exists(DATA_JS_PATH):
        with open(DATA_JS_PATH, "r", encoding="utf-8") as f:
            text = f.read()
            idx = text.find("{")
            r_idx = text.rfind("}")
            if idx != -1 and r_idx != -1:
                return json.loads(text[idx : r_idx + 1])
    return {"meta": {}, "community_projects": [], "company_timeline": []}


def save_feed(data: dict):
    data.setdefault("meta", {})
    data["meta"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    with open(DATA_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    js_content = (
        "// AI Pulse Radar - 自动生成的数据源 (请勿破坏 JSON 结构)\n"
        "window.AI_RADAR_DATA = "
        + json.dumps(data, ensure_ascii=False, indent=2)
        + ";\n"
    )
    with open(DATA_JS_PATH, "w", encoding="utf-8") as f:
        f.write(js_content)


def main():
    print("📡 [AI 极客雷达] 开始扫描全球一手 AI 极客社区...")
    feed = load_existing_feed()

    raw_items = []
    raw_items.extend(fetch_simon_willison())
    raw_items.extend(fetch_hacker_news_ai())
    raw_items.extend(fetch_reddit_feeds())
    print(f"✅ 成功抓取 {len(raw_items)} 条一手原始社区帖。")

    api_key = load_env_key()
    if not api_key:
        print("ℹ️ 未检测到 DEEPSEEK_API_KEY，保留当前精选库并同步生成 data/feed.json。")
        save_feed(feed)
        return

    if not raw_items:
        print("⚠️ 本次未抓到外部网络源，保留现有数据。")
        save_feed(feed)
        return

    print("🧠 正在调用 DeepSeek API 提纯野生评测、复现 Prompt 与大事记...")
    try:
        digested = call_deepseek_digest(api_key, raw_items)
        existing_p_ids = {p.get("id") for p in feed.get("community_projects", [])}
        new_projects = [
            p for p in digested.get("new_projects", []) if p.get("id") not in existing_p_ids
        ]
        # 保留镇馆之宝（带 SVG 预览的经典项目）并把最新提纯的排在前面
        pinned = [p for p in feed.get("community_projects", []) if p.get("svg_preview")]
        others = [p for p in feed.get("community_projects", []) if not p.get("svg_preview")]
        feed["community_projects"] = pinned[:2] + new_projects + pinned[2:] + others[:12]

        existing_t_ids = {t.get("id") for t in feed.get("company_timeline", [])}
        new_timeline = [
            t for t in digested.get("new_timeline", []) if t.get("id") not in existing_t_ids
        ]
        feed["company_timeline"] = (new_timeline + feed.get("company_timeline", []))[:15]

        print(f"🎉 DeepSeek 提纯完成！新增 {len(new_projects)} 个野生项目卡片，{len(new_timeline)} 条大事记。")
    except Exception as e:
        print(f"❌ DeepSeek 提纯出错: {e}")

    save_feed(feed)
    print("💾 数据已同步写入 data/feed.js 与 data/feed.json！")


if __name__ == "__main__":
    main()
