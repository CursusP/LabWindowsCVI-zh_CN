#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定位项目根目录。

源码运行时是仓库根；Nuitka 打包成单文件 exe 后，`__file__` 指向临时解包目录，
因此按「脚本 → argv[0] → 解释器」三个起点向上找 `tm/core_entries.json`，
找到的那一级就是根目录。tm/ 会随 exe 一起打包，所以两种运行方式都能命中。
"""
import os
import sys

MARKER = os.path.join("tm", "core_entries.json")


def find_root():
    seeds = []
    for raw in (__file__, sys.argv[0] if sys.argv and sys.argv[0] else None, sys.executable):
        if not raw:
            continue
        p = os.path.abspath(raw)
        seeds.append(p if os.path.isdir(p) else os.path.dirname(p))

    seen = set()
    for start in seeds:
        d = start
        for _ in range(5):
            if d in seen or not d:
                break
            seen.add(d)
            if os.path.isfile(os.path.join(d, MARKER)):
                return d
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


ROOT = find_root()
