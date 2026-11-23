#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""译文表的静态检查（不需要安装 CVI，可在 CI 里跑）。

与 tmcheck.py 的分工：
  * lint_tm.py  —— 只看 tm/ 自身：格式、重复 ID、编码、引号、字段数。任何机器都能跑。
  * tmcheck.py  —— 需要本机英文原版 cvimsgs.txt：比对格式说明符与换行数。只有译者本地能跑。

用法：
    python tools/lint_tm.py            # 检查 tm/*.tsv
    python tools/lint_tm.py tm/x.tsv   # 只查指定文件
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = re.compile(r"%[-+ 0#]*\d*(?:\.\d+)?[diouxXeEfgGcsS%]")
WELCOME = "welcome.tsv"


def has_bare_quote(s):
    """是否存在未转义的双引号。连续反斜杠为偶数时，后面的引号未被转义。"""
    i = s.find('"')
    while i >= 0:
        n, j = 0, i - 1
        while j >= 0 and s[j] == "\\":
            n += 1
            j -= 1
        if n % 2 == 0:
            return True
        i = s.find('"', i + 1)
    return False


def check_file(path, seen):
    """返回 (条目数, 问题列表)。"""
    name = os.path.basename(path)
    problems = []
    rows = 0
    is_welcome = name == WELCOME

    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\xef\xbb\xbf"):
        body = raw[3:]
    else:
        body = raw
        if not is_welcome:
            problems.append("缺少 UTF-8 BOM（Excel 直接打开会乱码，建议加 BOM）")

    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as e:
        return 0, [f"不是合法的 UTF-8：{e}"]

    if b"\r\n" in body and body.count(b"\n") != body.count(b"\r\n"):
        problems.append("换行风格不统一（CRLF 与 LF 混用）")

    for no, line in enumerate(text.split("\n"), 1):
        line = line.rstrip("\r")
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            continue

        parts = line.split("\t")
        if len(parts) < 2:
            problems.append(f"第 {no} 行：缺少 TAB 分隔 → {line[:60]!r}")
            continue
        key, zh = parts[0].strip(), "\t".join(parts[1:])
        if not key:
            problems.append(f"第 {no} 行：key 为空")
            continue

        if is_welcome:
            rows += 1
        else:
            if not key.isdigit():
                problems.append(f"第 {no} 行：ID 不是数字 → {key!r}")
                continue
            mid = int(key)
            if mid in seen:
                problems.append(f"第 {no} 行：ID {mid} 与 {seen[mid]} 重复")
            else:
                seen[mid] = f"{name}:{no}"
            rows += 1

        if not zh.strip():
            problems.append(f"第 {no} 行（{key}）：译文为空")
            continue
        if has_bare_quote(zh):
            problems.append(f"第 {no} 行（{key}）：含未转义的双引号，会破坏字面量")
        try:
            zh.encode("gbk")
        except UnicodeEncodeError as e:
            problems.append(f"第 {no} 行（{key}）：无法以 GBK 编码（{e.reason}）")
    return rows, problems


def main(argv):
    files = argv[1:] or sorted(glob.glob(os.path.join(ROOT, "tm", "*.tsv")))
    if not files:
        print("!! tm/ 下没有 .tsv")
        return 1

    seen, total, bad_files = {}, 0, 0
    for path in files:
        rows, problems = check_file(path, seen)
        total += rows
        mark = "ok  " if not problems else "FAIL"
        print(f"[{mark}] {os.path.basename(path):28} {rows:5} 条")
        for p in problems[:20]:
            print(f"        - {p}")
        if len(problems) > 20:
            print(f"        … 另有 {len(problems) - 20} 条")
        if problems:
            bad_files += 1

    print(f"\n{len(files)} 个文件，{total} 条译文，{bad_files} 个文件有问题")
    return 1 if bad_files else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
