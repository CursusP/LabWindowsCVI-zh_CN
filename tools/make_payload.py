#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从本地 LabWindows/CVI 安装生成 payload/。

设计原则：仓库不附带任何 NI 二进制文件。使用者用自己的安装副本生成补丁载荷，
再由 install.bat（或 Setup.exe）写入安装目录。既避免再分发厂商二进制，
也保证载荷与本地版本完全一致。

用法：
    python tools/make_payload.py --cvi "C:/Program Files (x86)/National Instruments/CVI2015"
不给 --cvi 时按 CVI_ROOT 环境变量 → 注册表 → Program Files 的顺序自动探测。

本模块同时被 Setup.exe 调用：build() 是纯函数，不启动子进程。
"""
import argparse
import json
import os
import re
import shutil
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cviroot
import paths
import patch
import msgpatch

ROOT = paths.ROOT
MESSAGES_TOTAL = "8586"
EXPECTED_FILES = 11          # 9 个二进制 + cvimsgs.txt + welcome.ini/dll 中的现有项


def log(msg):
    print(msg, flush=True)


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def check_pristine(cvi):
    """确认源为英文原版，避免在已汉化文件上二次加工。"""
    p = os.path.join(cvi, "bin", "cvimsgs.txt")
    if not os.path.exists(p):
        raise SystemExit("!! 找不到 %s" % p)
    raw = read_bytes(p)
    non_ascii = sum(1 for b in raw if b > 127)
    header = raw.split(b"\r\n")[0].decode("ascii", "replace")
    if non_ascii:
        raise SystemExit(
            "!! 源目录已经是汉化版（cvimsgs.txt 含 %d 个非 ASCII 字节）。\n"
            "   请先运行 restore.bat 还原，或在干净的安装副本上生成。" % non_ascii)
    return header


def prepare_payload(payload):
    """清空上一次生成的载荷。

    载荷目录是纯生成物，残留的旧文件不会进 _files.txt，但会让目录与清单对不上，
    也会在排查“为什么装了旧版”时误导人。只清理「看起来就是载荷」的目录，
    避免用户误把 --out 指向别的目录时被清空。
    """
    if not os.path.isdir(payload):
        return
    entries = os.listdir(payload)
    if entries and not ({"_files.txt", "_manifest.json"} & set(entries)):
        raise SystemExit("!! %s 非空且不像载荷目录，拒绝清理；请换一个空目录。" % payload)
    for name in entries:
        p = os.path.join(payload, name)
        if os.path.isdir(p):
            shutil.rmtree(p)
        else:
            os.remove(p)


def load_welcome_tm():
    tm = {}
    tm_path = os.path.join(ROOT, "tm", "welcome.tsv")
    if not os.path.exists(tm_path):
        return tm
    with open(tm_path, encoding="utf-8-sig") as f:
        for ln in f:
            if not ln.strip() or "\t" not in ln:
                continue
            k, v = ln.rstrip("\n").split("\t", 1)
            tm[k.strip()] = v.strip()
    return tm


def build_welcome_ini(cvi, dst, tm=None):
    src = os.path.join(cvi, "WelcomePage", "welcome.ini")
    if not os.path.exists(src):
        log("   ! 未找到 welcome.ini，跳过")
        return False
    tm = load_welcome_tm() if tm is None else tm

    text = read_bytes(src).decode("gbk", errors="surrogateescape")
    hits = [0]

    def repl(m):
        key = m.group(2)
        if key in tm:
            hits[0] += 1
            return '%s"%s"' % (m.group(1), tm[key])
        return m.group(0)

    out = re.sub(r'(?m)^(\s*Title\s*=\s*)"([^"]*)"', repl, text)
    # StartupCheckStr 的值同时是欢迎页复选框标签（dll 去掉前缀后显示），
    # 必须与 welcome_page.dll 内的字符串保持一致，否则勾选状态无法记忆
    out = re.sub(r'(?m)^(\s*StartupCheckStr\s*=\s*)"([^"]*)"', repl, out)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "wb") as f:
        f.write(out.encode("gbk", errors="surrogateescape"))
    log("   welcome.ini：替换 %d 条" % hits[0])
    return True


def build_welcome_dll(cvi, dst, tm=None):
    """欢迎页控件文字在 welcome_page.dll 的 .rdata 内，按同长度限制原位覆写。"""
    src = os.path.join(cvi, "WelcomePage", "welcome_page.dll")
    if not os.path.exists(src):
        log("   ! 未找到 welcome_page.dll，跳过")
        return False
    tm = load_welcome_tm() if tm is None else tm

    raw = bytearray(read_bytes(src))
    hits = 0
    for k, v in tm.items():
        kb, vb = k.encode("gbk"), v.encode("gbk")
        # 先确认这条串真的在这个 dll 里。欢迎页大部分文字在 welcome.ini，
        # 不先判断就会给「New 3→4 字节」这类根本不存在的串报超长，看着像漏译。
        if b"\x00" + kb + b"\x00" not in raw:
            continue
        if len(vb) > len(kb):
            log("   ! 超长跳过：%s（%d → %d 字节）" % (k, len(kb), len(vb)))
            continue
        # 必须整串匹配：左边是 NUL（串起点）且右边是 NUL，
        # 否则 "Open" 会命中 "ExplorerOpen"、"Project" 会命中 "NewEmptyProject"
        start = 0
        needle = b"\x00" + kb + b"\x00"
        while True:
            i = raw.find(needle, start)
            if i < 0:
                break
            p = i + 1
            raw[p:p + len(kb)] = vb + b"\x00" * (len(kb) - len(vb))
            hits += 1
            start = i + 1 + len(kb)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "wb") as f:
        f.write(bytes(raw))
    log("   welcome_page.dll：替换 %d 处" % hits)
    return hits > 0


def build(cvi, payload=None, skip_binaries=False):
    """生成载荷，返回写入的文件相对路径列表。"""
    payload = payload or os.path.join(ROOT, "payload")
    cvi = os.path.abspath(cvi)
    if not os.path.exists(os.path.join(cvi, "cvi.exe")):
        raise SystemExit("!! 不是有效的 CVI 安装目录：%s" % cvi)

    log("源目录：%s" % cvi)
    header = check_pristine(cvi)
    if not header.startswith(MESSAGES_TOTAL):
        log("   ! 头部为 %r，与预期的 %s 条不一致（版本可能不同）" % (header, MESSAGES_TOTAL))
    log("   cvimsgs.txt 头部：%s（英文原版已确认）" % header)

    prepare_payload(payload)
    os.makedirs(os.path.join(payload, "bin"), exist_ok=True)
    files = []

    # 1) 二进制内嵌字符串
    if not skip_binaries:
        log("\n[1/3] 应用二进制内嵌字符串补丁 ...")
        patch.cmd_apply(SimpleNamespace(src=cvi, out=payload))
        mf = os.path.join(payload, "_manifest.json")
        if not os.path.exists(mf):
            raise SystemExit("!! 二进制补丁未产出 _manifest.json")
        with open(mf, encoding="utf-8") as f:
            manifest = json.load(f)
        for item in manifest["files"]:
            files.append(item["file"].replace("\\", "/"))

    # 2) 运行时消息目录
    log("\n[2/3] 应用消息目录翻译 ...")
    msgpatch.cmd_apply(SimpleNamespace(src=os.path.join(cvi, "bin"),
                                       out=os.path.join(payload, "bin")))
    files.append("bin/cvimsgs.txt")

    # 3) 欢迎页
    log("\n[3/3] 处理欢迎页配置 ...")
    tm = load_welcome_tm()
    if build_welcome_ini(cvi, os.path.join(payload, "WelcomePage", "welcome.ini"), tm):
        files.append("WelcomePage/welcome.ini")
    if build_welcome_dll(cvi, os.path.join(payload, "WelcomePage", "welcome_page.dll"), tm):
        files.append("WelcomePage/welcome_page.dll")

    files = sorted(set(files))
    with open(os.path.join(payload, "_files.json"), "w", encoding="utf-8") as f:
        json.dump({"files": files}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(payload, "_files.txt"), "wb") as f:
        f.write(("\r\n".join(files) + "\r\n").encode("ascii"))

    log("\n完成：%d 个文件写入 %s" % (len(files), payload))
    for f in files:
        log("   %s" % f)
    if len(files) < EXPECTED_FILES:
        log("\n   ! 只生成了 %d 个文件（完整安装通常为 %d 个）。"
            % (len(files), EXPECTED_FILES))
        log("     若安装目录缺少组件，或 CVI 版本不符，缺失的文件不会被替换。")
    return files


def main():
    ap = argparse.ArgumentParser(description="从本机 CVI 安装生成中文载荷")
    ap.add_argument("--cvi", default=None, help="CVI 安装根目录；省略则自动探测")
    ap.add_argument("--out", default=None, help="载荷输出目录；默认仓库内 payload/")
    ap.add_argument("--skip-binaries", action="store_true", help="只生成文案载荷")
    a = ap.parse_args()

    build(cviroot.find(a.cvi), a.out, a.skip_binaries)


if __name__ == "__main__":
    main()
