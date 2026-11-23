#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI & 量化研究一手雷达 · 抓取 + DeepSeek 提纯
================================================
用法：
    python3 fetch_and_digest.py            # 抓取全部来源并用 DeepSeek 提纯（需要 DEEPSEEK_API_KEY）
    python3 fetch_and_digest.py --no-llm   # 只抓取，不调用模型（摘要退化为原文片段）

核心权重优先级：
1. 量化与数理研究效率 Skills / MCP / 工具（统计学、金融市场、金融数学、计量经济学、量化金融、宏观经济学）
2. 好玩的可视化与交互项目（带真实 Prompt、可在线体验或可视化实证）
3. 去同质化的一手 AI 社区情报与大厂通告（全部直达原始出处）
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

UA = "ai-quant-radar/3.0 (+https://github.com/sxy3481841323-ship-it/ai-pulse-radar)"
NOW = datetime.now(timezone.utc)
DIGEST_MODEL = os.environ.get("RADAR_MODEL", "deepseek-flash")
COMMUNITY_KEEP_DAYS = 10
COMMUNITY_MAX = 80
OFFICIAL_KEEP_DAYS = 30
OFFICIAL_MAX = 36
QUANT_MAX = 24
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
# 优先级 #1：量化研究（统计学 / 金融市场 / 金融数学 / 计量经济学 / 量化金融 / 宏观经济学）Skills & 工具源
# ----------------------------------------------------------------------------
# 每个种子条目都会向 GitHub API 实时拉取最新的 stars、pushed_at、html_url、description，
# 同时附上针对量化研究工作流的 Agent Skill 提示词模板与安装/调用方式。
QUANT_SKILL_SEEDS = [
    {
        "repo": "microsoft/qlib",
        "discipline": "quant_fin",
        "discipline_label": "量化金融",
        "kind": "AI 量化投研平台 & Skill",
        "title_zh": "Qlib · 微软面向 AI 的全链路量化投研与因子挖掘引擎",
        "efficiency_gain": "内置 Alpha158/360 因子库、LightGBM/Transformer 截面预测与组合优化器，支持将『因子表达式构建 → IC/IR 衰减检验 → 分层回测』封装为自动化 Agent Skill。",
        "install_cmd": "pip install pyqlib",
        "skill_recipe": "【Claude/Cursor Quant Skill 提示词】基于 Qlib 的 DataHandlerLP 构建截面因子表达式：请将以下经济学假设转化为 Qlib 算子表达式（使用 Ref, Mean, Std, Corr, Rank），并输出包含 IC、RankIC、年化超额与换手率惩罚的完整分层回测脚本。",
        "visual_preview": "alpha_ic_curve",
        "metrics_badge": "IC / RankIC / Alpha360"
    },
    {
        "repo": "OpenBB-finance/OpenBB",
        "discipline": "market",
        "discipline_label": "金融市场",
        "kind": "金融数据终端 & MCP Server",
        "title_zh": "OpenBB Platform · 统一接入全球股票、期权链、宏观与财报的开源终端",
        "efficiency_gain": "提供标准化的 Python SDK 与 FastAPI / MCP 接口，一行命令挂载到大模型 Agent，即可直接拉取实时美股期权隐含波动率曲面、FOMC 收益率曲线与跨市场资金流。",
        "install_cmd": "pip install openbb && openbb-api",
        "skill_recipe": "【MCP 挂载与提示词】启动 `openbb-api` 后挂载至 Agent：请调用 obb.derivatives.options.chains 拉取 SPY 近月与远月期权链，计算 25-Delta Risk Reversal 与隐含波动率期限结构斜率，并识别异常大单成交。",
        "visual_preview": "iv_term_structure",
        "metrics_badge": "Equities · Options · Macro MCP"
    },
    {
        "repo": "py-econometrics/pyfixest",
        "discipline": "econometrics",
        "discipline_label": "计量经济学",
        "kind": "高维固定效应与因果推断引擎",
        "title_zh": "PyFixest · 复刻 R 语言 fixest 的极速高维固定效应与双重差分（DID）库",
        "efficiency_gain": "在面板数据回归、事件研究（Event Study）、交错双重差分（Sun & Abraham / Callaway & Sant'Anna）与多维聚类标准误计算上比传统方法快一个数量级，极适合因子事件检验。",
        "install_cmd": "pip install pyfixest",
        "skill_recipe": "【计量经济学 Skill 提示词】请使用 pyfixest 的 feols() 编写面板回归与动态事件研究（Event Study）：控制个体与时间双向固定效应（entity + time FE），采用双向聚类稳健标准误（CRV1），并检验平行趋势假设与脉冲响应置信区间。",
        "visual_preview": "did_event_study",
        "metrics_badge": "HDFE · DID · Cluster SE"
    },
    {
        "repo": "bashtage/arch",
        "discipline": "econometrics",
        "discipline_label": "计量经济学",
        "kind": "波动率计量与单位根检验核心库",
        "title_zh": "ARCH · 金融时间序列 GARCH 族波动率建模、协整与 Bootstrap 计量库",
        "efficiency_gain": "涵盖 GARCH / EGARCH / TARCH / FIGARCH 条件异方差建模、ADF/KPSS/Phillips-Perron 单位根检验、Engle-Granger 协整检验与 Stationary Bootstrap，是统计套利与波动率预测的基石。",
        "install_cmd": "pip install arch",
        "skill_recipe": "【波动率计量 Skill 提示词】请使用 arch 库对资产日频对数收益率拟合 GJR-GARCH(1,1,1) 并采用 Student-t 新息分布，提取条件波动率序列，计算 99% 动态 VaR / Expected Shortfall，并进行 Kupiec 失败率回测检验。",
        "visual_preview": "garch_vol_cone",
        "metrics_badge": "GJR-GARCH · VaR · Cointegration"
    },
    {
        "repo": "Nixtla/statsforecast",
        "discipline": "stat",
        "discipline_label": "统计学",
        "kind": "高频统计时序预测引擎",
        "title_zh": "StatsForecast · Numba 加速的高性能统计与计量时间序列预测套件",
        "efficiency_gain": "比传统 ARIMA/ETS 实现快 20~50 倍，内置 AutoARIMA、AutoETS、AutoCES、MSTL 多重季节分解与共形预测区间（Conformal Prediction Intervals），支持百万级截面时序并行。",
        "install_cmd": "pip install statsforecast",
        "skill_recipe": "【统计学时序 Skill 提示词】使用 StatsForecast 构建带非参数共形预测区间（ConformalIntervals）的多模型集成（AutoARIMA + AutoETS + DynamicOptimizedTheta），采用滚动窗口交叉验证（cross_validation）评估 CRPS 与 MASE。",
        "visual_preview": "conformal_fan",
        "metrics_badge": "AutoARIMA · Conformal CI"
    },
    {
        "repo": "dcajasn/Riskfolio-Lib",
        "discipline": "fin_math",
        "discipline_label": "金融数学",
        "kind": "凸优化与尾部风险组合数学库",
        "title_zh": "Riskfolio-Lib · 均值-CVaR、嵌套聚类（NCO）与风险平价组合数学优化引擎",
        "efficiency_gain": "支持 24 种凸风险度量（CVaR、CDaR、EVaR、Entropic Risk、鲁棒椭球不确定集）、Ledoit-Wolf 收缩协方差矩阵、Black-Litterman 贝叶斯观点融合与层次风险平价（HRP）。",
        "install_cmd": "pip install riskfolio-lib",
        "skill_recipe": "【金融数学组合优化 Skill 提示词】请使用 Riskfolio-Lib 构建鲁棒均值-CVaR（Conditional Value-at-Risk）组合优化：采用 Ledoit-Wolf 收缩估计与 Gerber 统计协方差，加入单资产权重上限与行业中性线性约束，并绘制有效前沿风险贡献分解图。",
        "visual_preview": "cvar_frontier",
        "metrics_badge": "CVaR · HRP · Black-Litterman"
    },
    {
        "repo": "lballabio/QuantLib",
        "discipline": "fin_math",
        "discipline_label": "金融数学",
        "kind": "衍生品定价与随机分析工业标准",
        "title_zh": "QuantLib · 期权波动率曲面校准、利率期限结构与蒙特卡洛 PDE 定价引擎",
        "efficiency_gain": "覆盖 Heston / SABR / 局部波动率（Dupire）校准、无套利收益率曲线 Bootstrap、有限差分 PDE 求解器与奇异期权（Barrier / Asian / Bermudan）定价。",
        "install_cmd": "pip install QuantLib",
        "skill_recipe": "【衍生品定价 Skill 提示词】请使用 QuantLib-Python 构建 HestonModel 与 AnalyticHestonEngine，基于给定的市场期权隐含波动率矩阵，使用 Levenberg-Marquardt 算法校准 (v0, kappa, theta, sigma, rho) 五个参数并输出拟合残差。",
        "visual_preview": "sabr_smile",
        "metrics_badge": "Heston · SABR · PDE Solver"
    },
    {
        "repo": "nautechsystems/nautilus_trader",
        "discipline": "quant_fin",
        "discipline_label": "量化金融",
        "kind": "Rust 内核高频事件驱动回测与实盘引擎",
        "title_zh": "NautilusTrader · Rust 编写的高性能 L2/L3 订单簿微观结构回测与执行引擎",
        "efficiency_gain": "回测与实盘完全共用一套事件驱动代码，原生支持 L2/L3 限价订单簿（Order Book）撮合仿真、排队位置估计、延迟注入与多交易所并发。",
        "install_cmd": "pip install nautilus_trader",
        "skill_recipe": "【高频微观结构 Skill 提示词】请基于 NautilusTrader 编写基于 L2 订单簿失衡度（Order Book Imbalance, OBI）与微价格（Micro-price）偏移的做市策略，纳入挂单排队延迟与 Maker/Taker 手续费结构。",
        "visual_preview": "lob_imbalance",
        "metrics_badge": "Rust Core · L2/L3 OrderBook"
    },
    {
        "repo": "akfamily/akshare",
        "discipline": "market",
        "discipline_label": "金融市场",
        "kind": "中文金融市场与宏观高频数据库",
        "title_zh": "AKShare · A 股、国债收益率曲线、商品期货基差与中美宏观指标开源数据接口",
        "efficiency_gain": "一站式拉取中债国债收益率曲线、沪深300/中证1000期权隐波、大宗商品库存与基差、北向/融资融券及中美 CPI/PMI/社融宏观序列，是构建本土量化与宏观 Skill 的首选数据源。",
        "install_cmd": "pip install akshare --upgrade",
        "skill_recipe": "【跨资产宏观与市场 Skill 提示词】请调用 akshare 拉取近 5 年中债 10Y-2Y 国债期限利差、社融存量同比与沪深300 ERP（股权风险溢价），构建宏观状态马尔可夫区制转换（Markov Regime Switching）股债轮动信号。",
        "visual_preview": "yield_curve_erp",
        "metrics_badge": "A-Share · Futures · CN Macro"
    },
    {
        "repo": "polakowo/vectorbt",
        "discipline": "quant_fin",
        "discipline_label": "量化金融",
        "kind": "向量化超参数网格回测引擎",
        "title_zh": "vectorbt · 基于 NumPy + Numba 将万组策略参数在秒级一次性矩阵回测的利器",
        "efficiency_gain": "将传统的逐根 K 线 for 循环转化为三维张量广播运算，1 秒内完成 10,000 组参数组合的夏普比率、Sortino、Calmar 与最大回撤热力图检验，快速识别参数过拟合孤岛。",
        "install_cmd": "pip install vectorbt",
        "skill_recipe": "【向量化回测与防过拟合 Skill 提示词】请使用 vectorbt 对均线/波动率突破策略进行二维参数网格向量化回测，计算 Deflated Sharpe Ratio（DSR）与概率夏普比率（PSR），剔除多重假设检验带来的伪显著参数区。",
        "visual_preview": "sharpe_heatmap",
        "metrics_badge": "Numba Tensor · DSR / PSR"
    },
    {
        "repo": "statsmodels/statsmodels",
        "discipline": "macro",
        "discipline_label": "宏观经济学",
        "kind": "宏观计量 SVAR / 状态空间卡尔曼滤波引擎",
        "title_zh": "Statsmodels (TSA & Statespace) · 结构向量自回归（SVAR）、马尔可夫区制转换与卡尔曼滤波",
        "efficiency_gain": "内置结构向量自回归（SVAR）短期/长期识别约束、脉冲响应函数（IRF）、方差分解（FEVD）、动态因子模型（DynamicFactorMQ，美联储 Nowcasting 同款）与 MarkovRegression。",
        "install_cmd": "pip install statsmodels",
        "skill_recipe": "【宏观经济学 Nowcasting & SVAR Skill 提示词】请使用 statsmodels.tsa.statespace.DynamicFactorMQ 构建混频宏观 GDP Nowcasting 状态空间模型（结合月度 PMI/工业增加值/信贷与季度 GDP），并输出卡尔曼平滑因子与脉冲响应图。",
        "visual_preview": "svar_irf",
        "metrics_badge": "SVAR · IRF · Kalman Nowcast"
    },
    {
        "repo": "DoubleML/doubleml-for-py",
        "discipline": "stat",
        "discipline_label": "统计学",
        "kind": "双重机器学习（DML）正交化因果统计引擎",
        "title_zh": "DoubleML · Chernozhukov 双重/去偏机器学习（Debiased ML）高维因果效应估计库",
        "efficiency_gain": "利用 Neyman 正交得分函数与交叉拟合（Cross-Fitting），在数百个高维混杂因子（Confounders）存在非线性关系时，依然能给出具有渐近正态分布的无偏处置效应估计与有效置信区间。",
        "install_cmd": "pip install doubleml",
        "skill_recipe": "【高维统计因果推断 Skill 提示词】请使用 DoubleMLPLR（部分线性回归模型）结合 RandomForest / LightGBM 作为干扰参数学习器，通过 5 折交叉拟合估计核心因子对远期收益的去偏因果边际效应（ATE）及 95% 渐近置信区间。",
        "visual_preview": "dml_ortho",
        "metrics_badge": "Neyman Orthogonal · Causal ML"
    }
]


def src_quant_skills():
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]

    def fetch_seed(seed):
        repo = seed["repo"]
        url = f"https://api.github.com/repos/{repo}"
        stars = None
        pushed_at = iso(NOW)
        desc = ""
        lang = "Python"
        topics = []
        try:
            data = http_json(url, headers)
            stars = data.get("stargazers_count")
            pushed_at = iso(parse_time(data.get("pushed_at") or data.get("updated_at")))
            desc = clean(data.get("description") or "", 240)
            lang = data.get("language") or "Python"
            topics = (data.get("topics") or [])[:5]
        except Exception:
            pass
        entry = dict(seed)
        entry.update({
            "id": make_id(f"https://github.com/{repo}"),
            "url": f"https://github.com/{repo}",
            "stars": stars,
            "pushed_at": pushed_at,
            "gh_description": desc,
            "language": lang,
            "topics": topics,
        })
        return entry

    with ThreadPoolExecutor(6) as ex:
        items = list(ex.map(fetch_seed, QUANT_SKILL_SEEDS))
    return items


# ----------------------------------------------------------------------------
# 社区来源（优先级 #2 好玩可视化项目 + 优先级 #3 去同质化一手社区资讯）
# ----------------------------------------------------------------------------
HN_QUERIES = ["LLM", "GPT", "Claude", "Gemini", "DeepSeek", "Qwen", "Kimi", "OpenAI",
              "Anthropic", "AI agent", "MCP", "quant", "time series", "benchmark AI"]
SHOW_HN_QUERIES = ["AI", "LLM", "Claude", "agent", "simulation", "quant", "visualizer"]


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
    for topic in ["llm", "ai-agent", "agents", "generative-ai", "mcp", "quantitative-finance"]:
        min_stars = 30 if topic == "quantitative-finance" else 150
        q = f"topic:{topic} created:>{since} stars:>={min_stars}"
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
QUANT_SOURCES = [
    ("GitHub 量化与数理研究库", src_quant_skills),
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


COMMUNITY_SYSTEM = """你是「量化与一手 AI 雷达」的主编。读者是一位专注量化金融（统计学、金融市场、金融数学、计量经济学、量化金融、宏观经济学）与硬核 AI 工程的研究者。
他的阅读权重优先级非常明确：
1. 能提升量化、统计建模、数据分析、Agent 自动化与编程效率的工具、Skill、MCP 与硬核开源项目；
2. 真正有意思、有可视化效果或交互 Demo、带具体玩法或 Prompt 的创意技术项目；
3. 高信噪比的一手极客社区技术突破与实测讨论（严禁同质化口水帖、严禁空洞营销和泛泛而谈的行业鸡汤）。

你会收到一组编号条目（来自 Hacker News、Simon Willison 博客、Lobsters、GitHub、Hugging Face、V2EX），包含标题、片段、热度和部分社区评论。

硬性规则：
1. 只能从给定条目中挑选，用 ref 编号引用。绝不编造任何事实、链接、数字、人名。
2. 强力去同质化：同一事件或同类套壳工具只保留含金量最高的一条；彻底剔除公关软文、招聘、无实质技术细节的泛泛观点。
3. 选 14~20 条，按「研究/工程实用价值 × 视觉或实测趣味性 × 社区热度」从高到低排序。
4. category 只能是：
   - "tool"  能提升研究/编程/自动化效率的新开源工具、Skill、MCP、量化与数据工程库
   - "play"  有直观可视化效果、可在线交互试玩、或者创意让人眼前一亮的实验项目
   - "bench" 野生硬核实测 / 模型能力边界对比 / 算法基准检验
   - "talk"  有深度技术洞见的一手社区高赞讨论
5. title_zh：精准洗练的中文标题，不标题党，不超过 32 个字。
6. why：2~3 句干货，直接说清「核心机制是什么」「为什么值得看 / 怎么用」，若给了评论则用一句话点出评论区最犀利的技术反馈。不超过 120 个字。
7. prompt：当片段或评论里出现了可复用的提示词或命令时摘录，否则为 null。
8. tags：2~3 个中文短标签。
9. fun：1~5，代表可视化或实操吸引力。

另外写一份今日简报 briefing：
- headline：一句话点透今日最值得关注的硬核工具或技术信号（不超过 28 字）。
- points：3~4 条，每条不超过 55 字，并在 refs 里列出支撑它的条目编号。

只输出合法 JSON（注意：中文文本内部如需引号请一律使用中文引号「」或『』，严禁在 JSON 字符串值内部出现未转义的英文双引号 "）：
{"briefing":{"headline":"...","points":[{"text":"...","refs":[1,2]}]},
 "picks":[{"ref":1,"category":"tool","title_zh":"...","why":"...","prompt":null,"tags":["..."],"fun":4}]}"""

OFFICIAL_SYSTEM = """你是「量化与一手 AI 雷达」的编辑，负责提炼 AI 大厂官方通告与一手模型发布。
规则：
1. 只依据给定文本，不编造任何信息。
2. title_zh：准确的中文标题，不超过 30 字。模型名、产品名保留英文原文。
3. summary_zh：一句话说明核心技术更新或对开发者/研究者的实际影响，不超过 60 字。
4. importance：3=新模型/新推理架构/重大 API 或 Agent 工具能力发布；2=有价值的研究论文、基准开源；1=公关通告、客户案例、泛泛访谈（importance=1 将被直接过滤剔除）。
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
    if not picks:
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
    print(f"📡 量化与一手 AI 雷达开始抓取 · {iso(NOW)} · 模型: {DIGEST_MODEL if key else '不使用'}")

    print("优先级 #1 · 量化与数理研究 Skills 源：")
    quant_skills, quant_status = run_sources(QUANT_SOURCES)
    print("优先级 #2/#3 · 社区来源：")
    community_raw, community_status = run_sources(COMMUNITY_SOURCES)
    print("优先级 #3 · 官方来源：")
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
        "schema": 3,
        "generated_at": iso(NOW),
        "model": DIGEST_MODEL if key else None,
        "quant_skills": quant_skills or prev.get("quant_skills", []),
        "briefing": briefing or prev.get("briefing"),
        "community": merge(community, prev.get("community"), COMMUNITY_KEEP_DAYS, COMMUNITY_MAX,
                           lambda x: (x.get("first_seen", "")[:10], -(x.get("rank") or 0))),
        "official": merge(official, prev.get("official"), OFFICIAL_KEEP_DAYS, OFFICIAL_MAX,
                          lambda x: x.get("published_at", "")),
        "hf_trending": hf_trending or prev.get("hf_trending", []),
        "sources": quant_status + community_status + official_status,
        "unavailable": [{"name": n, "reason": r} for n, r in UNAVAILABLE],
    }
    write_feed(feed)
    print(f"💾 完成：量化 Skills {len(feed['quant_skills'])} 条，社区 {len(feed['community'])} 条，官方 {len(feed['official'])} 条")


if __name__ == "__main__":
    main()
