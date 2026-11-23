#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用 DeepSeek 实跑 data/classics.json 里的经典测试，把模型输出保存成可直接打开的 demos/<测试id>/<模型>.html

    python3 make_demos.py                 # 只生成还没有的 Demo
    python3 make_demos.py --force         # 全部重新生成（比如模型更新后重测）
    python3 make_demos.py pelican-bicycle # 只跑某一个测试

运行记录（模型、耗时、token 数、生成时间）写回 classics.json 的 runs 字段，页面会展示。
"""

import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from fetch_and_digest import ROOT, CLASSICS_JSON, http, load_key, load_previous, write_feed

DEMO_DIR = os.path.join(ROOT, "demos")
MODEL_NAMES = {"deepseek-flash": "DeepSeek-V4.1-Flash", "deepseek-v4-pro": "DeepSeek-V4-Pro"}

SVG_WRAPPER = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>html,body{{margin:0;height:100%;background:#fff}}body{{display:flex;align-items:center;justify-content:center}}
svg{{max-width:96vw;max-height:96vh;width:auto;height:auto}}</style></head>
<body>
{svg}
</body></html>
"""


def call(key, model, prompt):
    payload = json.dumps({
        "model": model,
        "reasoning_effort": "low",
        "messages": [
            {"role": "system", "content": "Output only the requested self-contained code inside a code block. Keep code clean, complete, and under 350 lines."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 64000,
    }).encode()
    t0 = time.time()
    raw = http("https://api.deepseek.com/chat/completions",
               {"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
               data=payload, timeout=900)
    data = json.loads(raw)
    return data["choices"][0]["message"]["content"], data.get("usage", {}), round(time.time() - t0, 1)


def extract(text, kind):
    blocks = re.findall(r"```(?:[a-zA-Z0-9_-]*)\n(.*?)```", text, re.S)
    candidates = blocks + [text]
    if kind == "svg":
        for c in candidates:
            m = re.search(r"<svg[\s\S]*?</svg>", c)
            if m:
                return m.group(0)
    else:
        for c in candidates:
            m = re.search(r"<!DOCTYPE html[\s\S]*</html>|<html[\s\S]*</html>", c, re.I)
            if m:
                return m.group(0)
    raise ValueError("模型输出里没有找到可用的 " + kind)


def run_one(key, classic, model):
    out_dir = os.path.join(DEMO_DIR, classic["id"])
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{model}.html")
    print(f"  → {classic['id']} × {model} 生成中…")
    text, usage, secs = call(key, model, classic["prompt"])
    code = extract(text, classic["output"])
    if classic["output"] == "svg":
        code = SVG_WRAPPER.format(title=f"{classic['name_en']} · {MODEL_NAMES.get(model, model)}", svg=code)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"  ✓ {classic['id']} × {model}：{secs}s，{usage.get('completion_tokens', '?')} tokens")
    return {
        "model": model, "model_name": MODEL_NAMES.get(model, model),
        "file": f"demos/{classic['id']}/{model}.html",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seconds": secs, "completion_tokens": usage.get("completion_tokens"),
    }


def main():
    key = load_key()
    if not key:
        sys.exit("缺少 DEEPSEEK_API_KEY")
    force = "--force" in sys.argv
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    classics = json.load(open(CLASSICS_JSON, encoding="utf-8"))

    jobs = []
    for c in classics:
        if only and c["id"] not in only:
            continue
        done = {r["model"] for r in c.get("runs", []) if os.path.exists(os.path.join(ROOT, r["file"]))}
        for m in c["models"]:
            if force or m not in done:
                jobs.append((c, m))

    def work(job):
        c, m = job
        for attempt in range(2):
            try:
                return c["id"], run_one(key, c, m)
            except Exception as e:
                print(f"  ✗ {c['id']} × {m} 第 {attempt + 1} 次失败：{e}")
        return c["id"], None

    with ThreadPoolExecutor(4) as ex:
        results = list(ex.map(work, jobs))

    for cid, run in results:
        if not run:
            continue
        c = next(x for x in classics if x["id"] == cid)
        c["runs"] = [r for r in c.get("runs", []) if r["model"] != run["model"]] + [run]
        c["runs"].sort(key=lambda r: c["models"].index(r["model"]) if r["model"] in c["models"] else 99)

    with open(CLASSICS_JSON, "w", encoding="utf-8") as f:
        json.dump(classics, f, ensure_ascii=False, indent=2)
    prev = load_previous()
    if prev:
        write_feed(prev)  # 重新打包 feed.js，带上最新的 classics
    print("完成")


if __name__ == "__main__":
    main()
