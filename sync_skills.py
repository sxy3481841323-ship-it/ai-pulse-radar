#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
野生 AI 雷达 · 跨 Agent 技能双向自动同步工具 (`sync_skills.py`)
============================================================
仅使用 Python 标准库，确保任何 Agent（Antigravity / Claude Code / Codex / Cursor）
接手本项目或切换电脑后，都能自动补齐仓库技能并将新装技能回传到仓库。

用法：
    python3 sync_skills.py                     # 检查并将仓库 .agents/skills/ 中缺失的技能自动下载到本机全局技能目录
    python3 sync_skills.py --dry-run           # 仅检测缺失状态，不实际写入文件
    python3 sync_skills.py --target <dir>      # 指定本机目标全局技能目录
    python3 sync_skills.py --push <name> ...   # 把本机新装的技能同步回仓库 .agents/skills/（自动剔除 .git 与排查密钥）
"""

import argparse
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_SKILLS_DIR = os.path.join(ROOT, ".agents", "skills")

DEFAULT_LOCAL_DIRS = [
    os.path.expanduser("~/.gemini/config/skills"),
    os.path.expanduser("~/.claude/skills"),
    os.path.expanduser("~/.codex/skills"),
]

IGNORE_NAMES = {".git", "__pycache__", ".DS_Store", "node_modules"}
SECRET_RE = re.compile(r"(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{10,})")


def _ignore_filter(_dir, names):
    return [n for n in names if n in IGNORE_NAMES]


def discover_local_dirs(explicit_targets=None):
    """返回需要同步的本机全局技能目录列表。"""
    if explicit_targets:
        return [os.path.abspath(os.path.expanduser(t)) for t in explicit_targets]
    found = [d for d in DEFAULT_LOCAL_DIRS if os.path.isdir(d)]
    if not found:
        # 若均尚未初始化，默认初始化到 ~/.gemini/config/skills
        found = [DEFAULT_LOCAL_DIRS[0]]
    return found


def list_valid_skills(base_dir):
    """列出目录下所有含有效 SKILL.md 的技能名与路径。"""
    if not os.path.isdir(base_dir):
        return {}
    out = {}
    for entry in sorted(os.listdir(base_dir)):
        full = os.path.join(base_dir, entry)
        if os.path.isdir(full) and os.path.isfile(os.path.join(full, "SKILL.md")):
            out[entry] = full
    return out


def scan_dir_for_secrets(skill_dir):
    """扫描文本文件中是否意外包含 API Key 或 GitHub Token。"""
    for root, dirs, files in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_NAMES]
        for fname in files:
            fpath = os.path.join(root, fname)
            if os.path.getsize(fpath) > 2 * 1024 * 1024:
                continue
            try:
                content = open(fpath, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            if SECRET_RE.search(content):
                return fpath
    return None


def pull_to_local(repo_skills, targets, dry_run=False):
    """检测本机缺失的仓库技能并自动补齐。"""
    total_copied = 0
    for target in targets:
        local_skills = list_valid_skills(target)
        missing = [name for name in repo_skills if name not in local_skills]
        print(f"📁 本机目录 {target}：已装 {len(local_skills)} 个，仓库待补齐 {len(missing)} 个")
        if not missing:
            continue
        if not dry_run:
            os.makedirs(target, exist_ok=True)
        for name in missing:
            src = repo_skills[name]
            dst = os.path.join(target, name)
            if dry_run:
                print(f"  [dry-run] 将下载同步: {name} -> {dst}")
            else:
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst, ignore=_ignore_filter)
                print(f"  ✓ 已自动补齐: {name} -> {dst}")
            total_copied += 1
    if total_copied == 0:
        print("✅ 本机所有已探测到的 Agent 技能目录均已与仓库保持同步。")
    return 0


def push_to_repo(skill_names, repo_skills_dir, sources, dry_run=False):
    """将本机新装的技能同步回仓库 .agents/skills/，自动过滤 .git 与密钥检查。"""
    os.makedirs(repo_skills_dir, exist_ok=True)
    # 同时扫描默认的几个本机技能目录，找出对应名称的技能
    candidates_map = {}
    for sdir in sources:
        for name, path in list_valid_skills(sdir).items():
            candidates_map.setdefault(name, path)

    synced = 0
    for name in skill_names:
        src = candidates_map.get(name)
        if not src:
            print(f"✗ 未在本机全局技能目录中找到有效技能（需含 SKILL.md）：{name}", file=sys.stderr)
            return 1
        leak = scan_dir_for_secrets(src)
        if leak:
            print(f"✗ 安全拦截：技能 {name} 中的文件 {leak} 疑似包含明文密钥，拒绝同步到仓库！", file=sys.stderr)
            return 1
        dst = os.path.join(repo_skills_dir, name)
        if dry_run:
            print(f"  [dry-run] 将回传至仓库: {src} -> {dst}")
        else:
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=_ignore_filter)
            print(f"  ✓ 已同步回仓库: {name} -> {dst}")
        synced += 1

    if synced and not dry_run:
        print("\n💡 提示：请别忘了将新增技能说明写入 AGENTS.md 的「共享技能速查表」和「交接日志」，然后 git commit && git push！")
    return 0


def main():
    parser = argparse.ArgumentParser(description="野生 AI 雷达 · 跨 Agent 技能双向自动同步工具")
    parser.add_argument("--dry-run", action="store_true", help="仅检查差异，不实际拷贝文件")
    parser.add_argument("--target", action="append", help="指定本机全局技能目录（可多次传入）")
    parser.add_argument("--push", nargs="+", metavar="SKILL_NAME", help="将本机新装的技能回传到仓库 .agents/skills/")
    args = parser.parse_args()

    repo_skills = list_valid_skills(REPO_SKILLS_DIR)
    print(f"📦 仓库 .agents/skills/ 共收录 {len(repo_skills)} 个共享技能")
    targets = discover_local_dirs(args.target)

    if args.push:
        return push_to_repo(args.push, REPO_SKILLS_DIR, targets, dry_run=args.dry_run)
    return pull_to_local(repo_skills, targets, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
