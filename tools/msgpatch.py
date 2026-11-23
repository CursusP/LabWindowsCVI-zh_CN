#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cvimsgs.txt 汉化应用器。

流程：读取 tm/*.tsv（ID<TAB>译文）→ 校验 → 写入副本 → 调 countmsg.exe 重算头部 → 回读校验。

校验项：
  1. 格式说明符（%s/%d/%ld/%.30s 等）序列必须与原文一致，顺序一致
  2. 转义序列 \\n 的数量必须一致（保证提示框换行结构不变）
  3. 译文不得包含裸双引号（会破坏文件字面量结构），也不得包含真实换行
用法：
  python msgpatch.py apply   [--src ...] [--out ...]
  python msgpatch.py verify  [--dir ...]
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from msgfile import MsgFile
import cviroot
import paths

ROOT = paths.ROOT
TM_DIR = os.path.join(ROOT, "tm")

SPEC_RE = re.compile(r"%[-+ 0#]*[0-9]*(?:\.[0-9]+)?(?:hh|h|ll|l|L|z|j|t)?[diouxXeEfgGaAcspn%]")


def load_tm():
    """读取所有 ID<TAB>译文 形式的表。

    同一 ID 在不同文件里给出不同译文时直接中止：后写入者静默覆盖前者的结果，
    会让「译文表里明明有这一条」和「界面上就是旧的」同时成立，极难排查。
    """
    rows, origin = {}, {}
    for path in sorted(glob.glob(os.path.join(TM_DIR, "*.tsv"))):
        name = os.path.basename(path)
        with open(path, encoding="utf-8-sig") as f:
            for ln_no, ln in enumerate(f, 1):
                ln = ln.rstrip("\n").rstrip("\r")
                if not ln.strip() or ln.lstrip().startswith("#"):
                    continue
                parts = ln.split("\t")
                if len(parts) < 2:
                    raise SystemExit("!! %s:%d 不是 TAB 分隔：%r" % (name, ln_no, ln))
                if not parts[0].strip().isdigit():
                    # 非 <ID>\t<译文> 形式的表（如 welcome.tsv）由各自的构建器处理，这里跳过
                    continue
                mid = int(parts[0].strip())
                zh = "\t".join(parts[1:])
                if mid in rows and rows[mid] != zh:
                    raise SystemExit(
                        "!! 译文冲突：ID %d 在 %s 与 %s:%d 中内容不同"
                        % (mid, origin[mid], name, ln_no))
                rows[mid] = zh
                origin.setdefault(mid, "%s:%d" % (name, ln_no))
    return rows


def specs(t):
    return [m.group() for m in SPEC_RE.finditer(t)]


def has_bare_quote(s):
    """是否存在未转义的双引号。

    只看前一个字符是不够的：`\\\\"` 里的引号其实未被转义，
    因此要数连续反斜杠的奇偶性。
    """
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


def check(en, zh):
    """返回拒绝原因，None 表示通过。"""
    if "\n" in zh or "\r" in zh:
        return "译文含真实换行，会拆断单行格式"
    if has_bare_quote(zh):
        return "译文含未转义的双引号"
    if specs(en) != specs(zh):
        return "格式符不一致 %s vs %s" % (specs(en), specs(zh))
    if en.count("\\n") != zh.count("\\n"):
        return "换行数不一致 %d vs %d" % (en.count("\\n"), zh.count("\\n"))
    try:
        zh.encode("gbk")
    except UnicodeEncodeError as exc:
        return "无法以 GBK 编码：%s" % exc
    return None


def resolve_bin_dir(src):
    """接受三种写法：bin 目录、CVI 安装根目录、cvimsgs.txt 文件本身。"""
    src = os.path.abspath(src)
    if os.path.isfile(src) and src.lower().endswith("cvimsgs.txt"):
        return os.path.dirname(src)
    if os.path.exists(os.path.join(src, "cvimsgs.txt")):
        return src
    if os.path.exists(os.path.join(src, "bin", "cvimsgs.txt")):
        return os.path.join(src, "bin")
    raise SystemExit("!! 在 %s 里找不到 cvimsgs.txt（既不是 bin 目录也不是安装根目录）" % src)


def cmd_apply(args):
    bin_dir = resolve_bin_dir(args.src)
    src = os.path.join(bin_dir, "cvimsgs.txt")
    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)

    # 先确认官方工具在位，再动文件：否则会留下一个头部未重算、加载器回退英文的产物
    cm = os.path.join(bin_dir, "countmsg.exe")
    if not os.path.exists(cm):
        raise SystemExit("!! 未找到 %s，无法重算头部；生成会产出英文界面，已中止。" % cm)

    try:
        m = MsgFile(src)
    except ValueError as exc:
        raise SystemExit("!! %s" % exc)
    tm = load_tm()

    applied, applied_ids, rejected, missing = 0, [], [], []
    for mid, zh in sorted(tm.items()):
        if mid not in m.items:
            missing.append(mid)
            continue
        en_raw = m.items[mid]
        why = check(en_raw, zh)
        if why:
            rejected.append((mid, en_raw, zh, why))
            continue
        m.items[mid] = zh
        applied_ids.append(mid)
        applied += 1

    out_path = os.path.join(out_dir, "cvimsgs.txt")
    m.save(out_path)

    # 用官方工具重算头部（条数/字节数）。头部不重算会被加载器静默回退英文，
    # 所以这里宁可中止，也不产出一个"看起来装好了但界面还是英文"的文件。
    # errors="replace"：countmsg 的输出按系统代码页走，中文 Windows 上若被按 UTF-8
    # 解码会抛 UnicodeDecodeError（同 cvi_running 那个坑），这里只用来显示，不该因解码失败中止。
    r = subprocess.run([cm, out_path, out_path + ".tmp"], capture_output=True,
                       text=True, errors="replace")
    if r.stdout.strip():
        print(r.stdout.strip())
    if r.returncode != 0:
        raise SystemExit("!! countmsg.exe 失败（退出码 %d）：%s" % (r.returncode, r.stderr.strip()))
    if not os.path.exists(out_path + ".tmp"):
        raise SystemExit("!! countmsg.exe 未产出临时文件，头部未重算")
    os.replace(out_path + ".tmp", out_path)

    # 回读校验：头部条数必须与实际条目数一致，已应用的 ID 必须逐条命中
    with open(out_path, "rb") as f:
        header = f.readline().decode("ascii", "replace").strip()
    fields = header.split()
    if len(fields) != 2 or not all(x.isdigit() for x in fields):
        raise SystemExit("!! 头部格式异常：%r" % header)
    check_file = MsgFile(out_path)
    if int(fields[0]) != len(check_file.items):
        raise SystemExit("!! 头部条数 %s 与实际 %d 不一致" % (fields[0], len(check_file.items)))
    mismatch = [mid for mid in applied_ids if check_file.items.get(mid) != tm[mid]]
    if mismatch:
        raise SystemExit("!! 回读校验失败，%d 条与译文表不一致（如 ID %s）"
                         % (len(mismatch), mismatch[0]))

    rep = {"applied": applied, "rejected": rejected, "missing": missing, "header": header}
    with open(os.path.join(out_dir, "_msg_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    print("\n已应用 %d 条；拒绝 %d 条；TM 中不存在的 ID %d 个" % (applied, len(rejected), len(missing)))
    for mid, en, zh, why in rejected[:15]:
        print("  ! %d: %s  %r -> %r" % (mid, why, en[:40], zh[:30]))
    if missing:
        print("  ! 未知 ID（前10）：%s" % missing[:10])
    print("新头部: %s" % header)


def cmd_verify(args):
    out_path = os.path.join(args.dir, "cvimsgs.txt")
    src = os.path.join(resolve_bin_dir(args.src), "cvimsgs.txt")
    m = MsgFile(out_path)
    base = MsgFile(src)
    tm = load_tm()
    bad = 0
    for mid, zh in sorted(tm.items()):
        if mid not in m.items:
            continue
        if m.items[mid] != zh:
            bad += 1
            print("  ! %d: 期望 %r 实际 %r" % (mid, zh, m.items[mid]))
    same = sum(1 for k in base.items if k in m.items and m.items[k] == base.items[k])
    print("校验：TM %d 条 → 文件内一致 %d 条，异常 %d 条" % (len(tm), len(tm) - bad, bad))
    print("条目总数 %d（原 %d），保持原文 %d 条" % (len(m.items), len(base.items), same))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="把译文写进 cvimsgs.txt 并重算头部")
    ap.add_argument("cmd", choices=["apply", "verify"])
    ap.add_argument("--src", default=None, help="CVI 的 bin 目录或安装根目录；省略则自动探测")
    ap.add_argument("--out", default=os.path.join(ROOT, "out", "patched_bin"))
    ap.add_argument("--dir", default=os.path.join(ROOT, "out", "patched_bin"))
    a = ap.parse_args()
    if not a.src:
        a.src = os.path.join(cviroot.find(), "bin")
    if a.cmd == "apply":
        cmd_apply(a)
    else:
        sys.exit(cmd_verify(a))
