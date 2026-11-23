#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定位 LabWindows/CVI 安装目录。

优先级：命令行参数 → 环境变量 CVI_ROOT → 注册表 → Program Files。
找不到就抛出 SystemExit 并给出可操作的提示，不做「猜一个路径」的兜底。
"""
import os
import sys

REG_KEYS = [
    r"SOFTWARE\WOW6432Node\National Instruments\CVI\15.0",
    r"SOFTWARE\National Instruments\CVI\15.0",
    r"SOFTWARE\WOW6432Node\National Instruments\CVI",
    r"SOFTWARE\National Instruments\CVI",
]
REG_VALUES = ["InstallDir", "Path", "InstallLocation"]


def normalize(raw):
    """接受带引号、带尾随反斜杠、指向 bin 子目录的写法，统一成安装根目录。"""
    if not raw:
        return None
    path = raw.strip().strip('"').strip()
    if not path:
        return None
    path = os.path.normpath(os.path.expandvars(path))
    if os.path.basename(path).lower() == "bin":
        path = os.path.dirname(path)
    return path


def is_cvi_dir(path):
    return bool(path) and os.path.exists(os.path.join(path, "cvi.exe"))


def _from_registry():
    if not sys.platform.startswith("win"):
        return None
    try:
        import winreg
    except ImportError:
        return None
    for key in REG_KEYS:
        for hive in (winreg.HKEY_LOCAL_MACHINE,):
            try:
                with winreg.OpenKey(hive, key) as k:
                    for name in REG_VALUES:
                        try:
                            val, _ = winreg.QueryValueEx(k, name)
                        except OSError:
                            continue
                        cand = normalize(val if isinstance(val, str) else None)
                        if is_cvi_dir(cand):
                            return cand
            except OSError:
                continue
    return None


def _from_env_dirs():
    for var in ("ProgramFiles(x86)", "ProgramFiles", "ProgramW6432"):
        base = os.environ.get(var)
        if not base:
            continue
        cand = os.path.join(base, "National Instruments", "CVI2015")
        if is_cvi_dir(cand):
            return cand
    return None


def find(explicit=None):
    """返回一个含 cvi.exe 的目录（绝对路径）。"""
    if explicit:
        path = os.path.abspath(normalize(explicit) or explicit)
        if not is_cvi_dir(path):
            raise SystemExit(
                "!! 目录里没有 cvi.exe：%s\n"
                "   请指向 LabWindows/CVI 的安装根目录，例如：\n"
                '   --cvi "C:\\Program Files (x86)\\National Instruments\\CVI2015"' % path
            )
        return path

    env = os.environ.get("CVI_ROOT")
    if env:
        path = os.path.abspath(normalize(env) or env)
        if is_cvi_dir(path):
            return path
        raise SystemExit("!! 环境变量 CVI_ROOT 指向的目录里没有 cvi.exe：%s" % path)

    for probe in (_from_registry, _from_env_dirs):
        path = probe()
        if path:
            return os.path.abspath(path)

    raise SystemExit(
        "!! 未找到 LabWindows/CVI 2015 安装目录。\n"
        "   任选一种方式指定：\n"
        '     1) 命令行加 --cvi "C:\\Program Files (x86)\\National Instruments\\CVI2015"\n'
        "     2) 设置环境变量 CVI_ROOT 指向安装根目录\n"
        "     3) 确认 CVI 已正常安装（注册表 HKLM\\SOFTWARE\\National Instruments\\CVI）"
    )


def find_cvimsgs(explicit=None):
    """找一个**英文原版** cvimsgs.txt，供 tmcheck / nlfix / report 比对用。

    顺序：显式路径 → 安装时留下的备份 → CVI 安装目录。
    跳过含非 ASCII 字节的（那是汉化后的文件，比对没有意义）。
    """
    cands = []
    if explicit:
        cands.append(explicit)
    local = os.environ.get("LOCALAPPDATA")
    if local:
        cands.append(os.path.join(local, "LabWindowsCVI-zh_CN", "backup", "bin", "cvimsgs.txt"))
    try:
        cands.append(os.path.join(find(), "bin", "cvimsgs.txt"))
    except SystemExit:
        pass

    checked = []
    for p in cands:
        if not p or not os.path.exists(p):
            continue
        checked.append(p)
        with open(p, "rb") as f:
            raw = f.read()
        if not any(b > 127 for b in raw):
            return p

    raise SystemExit(
        "!! 找不到英文原版 cvimsgs.txt。\n"
        "   已检查：\n" + "\n".join("     %s" % p for p in checked) +
        "\n   用 --src 显式指定，或先运行一次安装程序（它会保留原始文件备份）。"
    )
