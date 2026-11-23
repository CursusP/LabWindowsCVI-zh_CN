#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""输出项目的权威统计数字（README / COVERAGE 里引用的那些）。

数字只有一处来源：tm/ 与 payload/。改了译文或重新生成载荷后跑一次，
把结果抄进文档，避免「README 说 175、COVERAGE 说 174」这类自相矛盾。

用法：
    python tools/stats.py
    python tools/stats.py --md     # 输出可直接贴进表格的 Markdown
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOTAL_MSG = 8586          # cvimsgs.txt 的条目总数（英文原版头部），找不到原文件时使用


def message_total():
    """优先从英文原版/已生成载荷的头部读条目数，避免文档与数据脱节。"""
    for rel in ("backup/bin/cvimsgs.txt", "payload/bin/cvimsgs.txt"):
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        try:
            with open(p, "rb") as f:
                return int(f.readline().split()[0])
        except (OSError, ValueError, IndexError):
            continue
    return TOTAL_MSG


def tm_stats():
    files = [p for p in sorted(glob.glob(os.path.join(ROOT, "tm", "*.tsv")))
             if os.path.basename(p) != "welcome.tsv"]
    ids = set()
    for p in files:
        with open(p, encoding="utf-8-sig") as f:
            for line in f:
                key = line.split("\t", 1)[0].strip()
                if key.isdigit():
                    ids.add(int(key))
    welcome = 0
    wp = os.path.join(ROOT, "tm", "welcome.tsv")
    if os.path.exists(wp):
        with open(wp, encoding="utf-8-sig") as f:
            welcome = sum(1 for line in f if line.strip())
    return len(files), len(ids), welcome


def payload_stats():
    files_txt = os.path.join(ROOT, "payload", "_files.txt")
    manifest = os.path.join(ROOT, "payload", "_manifest.json")
    n_files = 0
    size = 0
    if os.path.exists(files_txt):
        with open(files_txt, encoding="utf-8") as f:
            rels = [x.strip() for x in f if x.strip()]
        n_files = len(rels)
        for rel in rels:
            p = os.path.join(ROOT, "payload", rel.replace("/", os.sep))
            if os.path.exists(p):
                size += os.path.getsize(p)
    n_patch = n_bin = 0
    if os.path.exists(manifest):
        with open(manifest, encoding="utf-8") as f:
            m = json.load(f)
        n_patch = sum(len(x["patches"]) for x in m.get("files", []))
        n_bin = len(m.get("files", []))
    return n_files, size, n_patch, n_bin


def main():
    md = "--md" in sys.argv
    n_tm, n_ids, n_wel = tm_stats()
    n_files, size, n_patch, n_bin = payload_stats()
    total_msg = message_total()
    pct = n_ids / total_msg * 100

    rows = [
        ("译文文件", f"{n_tm} 个 .tsv"),
        ("消息条目", f"{n_ids} 条（{pct:.1f}% / {total_msg}）"),
        ("欢迎页条目", f"{n_wel} 条"),
        ("二进制补丁", f"{n_patch} 处 / {n_bin} 个文件"),
        ("安装文件", f"{n_files} 个"),
        ("安装体积", f"{size / 1024 / 1024:.1f} MB"),
    ]
    if md:
        print("| 项 | 数值 |")
        print("|---|---|")
        for k, v in rows:
            print(f"| {k} | {v} |")
    else:
        for k, v in rows:
            print(f"{k:8} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
