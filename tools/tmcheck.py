#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只检查不落盘：列出 TM 中与原文格式/换行不匹配的条目。

用法： python tools/tmcheck.py [--src 英文cvimsgs.txt] [tm文件...]
不带参数则检查 tm/ 下全部 tsv，并用自动找到的英文原版比对。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from msgfile import MsgFile
from msgpatch import check, load_tm
import cviroot

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=None, help="英文原版 cvimsgs.txt；省略则自动查找")
    ap.add_argument("files", nargs="*", help="只检查这些 tsv")
    a = ap.parse_args()

    m = MsgFile(cviroot.find_cvimsgs(a.src))
    if a.files:
        rows = {}
        for p in a.files:
            p = p if os.path.isabs(p) else os.path.join(ROOT, p)
            for ln_no, ln in enumerate(open(p, encoding="utf-8-sig"), 1):
                ln = ln.rstrip("\r\n")
                if not ln.strip() or ln.lstrip().startswith("#"):
                    continue
                parts = ln.split("\t")
                if len(parts) < 2:
                    print(f"!! {os.path.basename(p)}:{ln_no} 非 TAB 分隔：{ln!r}")
                    continue
                key = parts[0].strip()
                if not key.isdigit():
                    continue      # welcome.tsv 等非 ID 表，跳过
                rows[int(key)] = "\t".join(parts[1:])
    else:
        rows = load_tm()

    bad = 0
    for mid, zh in sorted(rows.items()):
        if mid not in m.items:
            print(f"!! {mid} 原文不存在")
            bad += 1
            continue
        why = check(m.items[mid], zh)
        if why:
            bad += 1
            en = m.items[mid]
            print(f"-- {mid}: {why}")
            print(f"   EN({en.count(chr(92)+'n')}): {en[:160]!r}")
            print(f"   ZH({zh.count(chr(92)+'n')}): {zh[:160]!r}")
    print(f"\n检查 {len(rows)} 条，异常 {bad} 条")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
