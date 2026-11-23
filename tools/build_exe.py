#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 Nuitka 打包单文件安装程序 dist/LabWindowsCVI-zh_CN-Setup.exe。

必须在**目标运行时**的解释器里执行，因为 Nuitka 使用当前解释器自带的
CPython 头文件、静态库和运行时 DLL：

    py -3.8 -m pip install -r requirements-build.txt
    py -3.8 tools/build_exe.py

为什么固定 Python 3.8：CPython 3.9 起不再支持 Windows 7，而本项目的目标
用户里有相当一部分仍在使用 Win7 SP1。用 3.8 打包，产物才能在 Win7 上启动；
用 3.12/3.13 打包出来的 exe 只能在 Win8.1/10/11 上运行。

Nuitka 会自动下载配套的 MinGW-w64（--assume-yes-for-downloads），
首次构建需要联网，之后走缓存。
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON = os.path.join(ROOT, "assets", "icon.ico")
TM_DIR = os.path.join(ROOT, "tm")
ENTRY = os.path.join(ROOT, "tools", "setup.py")
OUT_NAME = "LabWindowsCVI-zh_CN-Setup.exe"
VERSION = "1.0.0.0"


def check_env(strict=True):
    problems = []
    if os.name != "nt":
        problems.append("只能在 Windows 上构建")
    if strict and sys.version_info[:2] != (3, 8):
        problems.append(
            "当前解释器是 Python %d.%d；只有 3.8 打包出的 exe 能在 Windows 7 上运行"
            "（加 --force 可跳过此检查，但产物不能声称支持 Windows 7）"
            % sys.version_info[:2])
    if not os.path.exists(ICON):
        problems.append("缺少图标 assets/icon.ico")
    if not os.path.exists(os.path.join(TM_DIR, "core_entries.json")):
        problems.append("缺少译文表 tm/core_entries.json")
    try:
        import nuitka  # noqa: F401
    except ImportError:
        problems.append("当前解释器没装 Nuitka：pip install -r requirements-build.txt")
    return problems


def main():
    ap = argparse.ArgumentParser(description="打包单文件安装程序")
    ap.add_argument("--output-dir", default=os.path.join(ROOT, "dist"))
    ap.add_argument("--keep-build", action="store_true", help="保留中间目录，便于排查构建问题")
    ap.add_argument("--force", action="store_true", help="跳过 Python 版本检查（产物不再支持 Windows 7）")
    a = ap.parse_args()

    problems = check_env(strict=not a.force)
    if problems:
        print("无法继续：")
        for p in problems:
            print("  - %s" % p)
        return 2
    if sys.version_info[:2] != (3, 8):
        print("! 已跳过版本检查：产物只能在 Windows 8.1 及以上运行。\n")

    os.makedirs(a.output_dir, exist_ok=True)
    cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        "--mingw64",
        "--assume-yes-for-downloads",
        "--disable-ccache",
        "--windows-console-mode=force",
        "--windows-icon-from-ico=%s" % ICON,
        # 安装器在用户机器上重新生成载荷，需要完整的 tm/ 译文表
        "--include-data-dir=%s=tm" % TM_DIR,
        "--output-dir=%s" % a.output_dir,
        "--output-filename=%s" % OUT_NAME,
        "--company-name=LabWindowsCVI-zh_CN",
        "--product-name=LabWindows/CVI 2015 zh-CN Language Pack",
        "--file-version=%s" % VERSION,
        "--product-version=%s" % VERSION,
        "--file-description=LabWindows/CVI 2015 Chinese language pack installer",
        ENTRY,
    ]
    if not a.keep_build:
        cmd.insert(3, "--remove-output")

    print("执行：\n  " + " \\\n  ".join(cmd) + "\n")
    rc = subprocess.call(cmd)
    if rc != 0:
        print("\n构建失败，退出码 %d" % rc)
        return rc

    exe = os.path.join(a.output_dir, OUT_NAME)
    if not os.path.exists(exe):
        print("\n构建结束但没有找到 %s" % exe)
        return 1
    print("\n完成：%s（%.1f MB）" % (exe, os.path.getsize(exe) / 1024 / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
