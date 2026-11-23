#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 TM 中译文的 \\n 数量对齐到原文。

CVI 的多行消息在源文件里靠 `\\n` 换行，换行位置只影响排版。
本工具在不改变文字内容的前提下，按标点拆分/合并片段，把数量对齐，
省去逐条手工数换行。

用法：
    python nlfix.py [--src 英文cvimsgs.txt] [--dry]
"""
import os, sys, glob, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from msgfile import MsgFile
import cviroot

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TM_DIR = os.path.join(ROOT, "tm")

SPLIT_AT = "，。；：、, "
JOIN_PREF = ("，", "。", "；", "：", "、", ",", " ", "")


def split_one(seg):
    """在 seg 中选择一个标点处一分为二，返回 (a, b) 或 None。"""
    best = None
    for i, ch in enumerate(seg):
        if ch in SPLIT_AT and 4 <= i <= len(seg) - 6:
            # 优先在靠中间的位置切
            score = abs(i - len(seg) / 2)
            if best is None or score < best[0]:
                best = (score, i, ch)
    if best is None:
        if len(seg) >= 12:
            mid = len(seg) // 2
            return seg[:mid], seg[mid:]
        return None
    _, i, ch = best
    if ch == " ":
        return seg[:i], seg[i + 1:]
    return seg[: i + 1], seg[i + 1:]


def join_two(a, b):
    """合并相邻两段。中文句子直接相接即可，不加空格。"""
    if not a:
        return b
    if not b:
        return a
    return a + b


def fit(segs, want):
    segs = [s for s in segs]
    guard = 0
    while len(segs) - 1 < want and guard < 200:
        guard += 1
        idx = max(range(len(segs)), key=lambda i: len(segs[i]))
        pair = split_one(segs[idx])
        if not pair:
            break
        segs[idx : idx + 1] = [pair[0], pair[1]]
    while len(segs) - 1 > want and len(segs) > 1:
        # 合并最短的相邻两段
        i = min(range(len(segs) - 1), key=lambda k: len(segs[k]) + len(segs[k + 1]))
        segs[i : i + 2] = [join_two(segs[i], segs[i + 1])]
    return segs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=None, help="英文原版 cvimsgs.txt；省略则自动查找")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    m = MsgFile(cviroot.find_cvimsgs(a.src))

    changed = 0
    for path in sorted(glob.glob(os.path.join(TM_DIR, "*.tsv"))):
        with open(path, "rb") as f:
            raw = f.read()
        bom = raw.startswith(b"\xef\xbb\xbf")
        lines = raw.decode("utf-8-sig").split("\n")
        out, dirty = [], False
        for ln in lines:
            if not ln.strip() or ln.lstrip().startswith("#") or "\t" not in ln:
                out.append(ln)
                continue
            mid_s, zh = ln.split("\t", 1)
            try:
                mid = int(mid_s.strip())
            except ValueError:
                out.append(ln)
                continue
            if mid not in m.items:
                out.append(ln)
                continue
            want = m.items[mid].count("\\n")
            got = zh.count("\\n")
            if want == got:
                out.append(ln)
                continue
            segs = fit(zh.split("\\n"), want)
            new = "\\n".join(segs)
            if new.count("\\n") == want:
                out.append(f"{mid}\t{new}")
                changed += 1
                dirty = True
                print(f"  {mid}: {got} -> {want}  {new[:48]}")
            else:
                out.append(ln)
                print(f"  ! {mid}: 无法自动对齐（{got} -> {want}），请手工处理")
        if dirty and not a.dry:
            # 保留原有 BOM，并强制 LF：文本模式默认会把 \n 换成 CRLF，破坏 tsv 的换行约定
            data = "\n".join(out).encode("utf-8")
            with open(path, "wb") as f:
                f.write((b"\xef\xbb\xbf" if bom else b"") + data)
    print(f"\n已对齐 {changed} 条" + ("（dry-run 未写盘）" if a.dry else ""))


if __name__ == "__main__":
    main()
