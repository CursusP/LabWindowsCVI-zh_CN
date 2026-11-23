#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""安装器入口（Nuitka 打包成单文件 exe）。

双击 = 安装；`--restore` = 还原英文。
负责：定位 CVI → 确认未在运行 → 生成载荷 → 备份 → 写入 → 汇报结果。
载荷与备份放在 %LOCALAPPDATA%\\LabWindowsCVI-zh_CN\\，不依赖 exe 所在目录
（exe 常被放在下载目录甚至临时目录，卸载风险高）。

退出码：
  0 成功（或已请求提权，实际工作在提权后的进程里）
  1 无需操作、用户放弃，或未找到 CVI 安装目录
  2 CVI 正在运行
  3 生成载荷失败、备份目录缺失或备份为空
  4 写入失败（已尝试回滚）
  5 权限不足，提权失败或被取消
  9 未预期异常
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cviroot

APP = "LabWindowsCVI-zh_CN"
VERSION = "v1.0"
NO_WINDOW = 0x08000000 if os.name == "nt" else 0
# 备份归属于哪一份 CVI 安装。只取原地改写的二进制体积——它们打补丁前后大小不变，
# 而 bin\cvimsgs.txt 是整份重写（461019 → 333173 字节），
# 若把它算进指纹，正常还原也会被误判成「跨版本」。
FP_FILES = ("cvi.exe", "cvi.dll", "compile.exe")


def base_dir():
    root = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
    d = os.path.join(root, APP)
    os.makedirs(d, exist_ok=True)
    return d


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def is_patched(cvi):
    p = os.path.join(cvi, "bin", "cvimsgs.txt")
    if not os.path.exists(p):
        return False
    return any(b > 127 for b in read_bytes(p))


def _running_by_snapshot():
    """用 Toolhelp 快照枚举进程名，返回 True/False；不可用时返回 None。

    不依赖 tasklist.exe：组策略、Server Core 或安全软件都可能移除/拦截它，
    而快照 API 自 Windows 2000 起就存在，也不需要解码控制台输出。
    """
    import ctypes
    from ctypes import wintypes

    TH32CS_SNAPPROCESS = 0x00000002
    INVALID = ctypes.c_void_p(-1).value

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", ctypes.c_wchar * 260),
        ]

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    k32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    k32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    k32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]

    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if not snap or snap == INVALID:
        return None
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(entry)
        ok = k32.Process32FirstW(snap, ctypes.byref(entry))
        while ok:
            if entry.szExeFile.lower() == "cvi.exe":
                return True
            ok = k32.Process32NextW(snap, ctypes.byref(entry))
        return False
    finally:
        k32.CloseHandle(snap)


def cvi_running():
    """CVI 是否在运行。

    优先用进程快照；快照不可用时退回 tasklist。退回路径绝对不能加 text=True：
    中文 Windows 上 tasklist 输出是 GBK，Python 若按 UTF-8 解码会在读线程里抛
    UnicodeDecodeError，stdout 变成 None，判断就永远返回 False —— 结果是
    「CVI 还开着也照样往下装」，最后所有文件写入失败。按字节匹配与代码页无关。
    """
    if os.name == "nt":
        try:
            state = _running_by_snapshot()
            if state is not None:
                return state
        except Exception:
            pass
    try:
        r = subprocess.run(["tasklist", "/fi", "imagename eq cvi.exe"],
                           capture_output=True, creationflags=NO_WINDOW)
    except OSError:
        return False
    if r.returncode != 0:
        return False
    return b"cvi.exe" in (r.stdout or b"").lower()


def ask(prompt):
    """等待用户输入；没有 stdin（脚本调用）时按默认处理。"""
    try:
        return input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return ""


# ---------------------------------------------------------------- 权限与提权

def is_admin():
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def can_write(path):
    """用一次真实写入探测，不看 ACL 字符串。

    CVI 默认装在 Program Files，普通用户在那里建文件会被拒；
    这里在安装根目录建一个空文件再删掉，能建就说明后续写入不会卡在权限上。
    """
    probe = os.path.join(path, ".cvi_l10n_probe")
    try:
        with open(probe, "wb"):
            pass
    except OSError:
        return False
    try:
        os.remove(probe)
    except OSError:
        pass
    return True


def launcher():
    """返回 (可执行文件, 重启时要带上的参数)，区分源码运行与单文件 exe。"""
    script = os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else ""
    if script.lower().endswith(".py"):
        # 源码方式：ShellExecuteW 无法直接执行 .py，必须先起解释器
        return sys.executable, [script] + sys.argv[1:]
    return sys.executable, sys.argv[1:]


def relaunch_elevated(extra_args):
    """以管理员身份重启自身（UAC 只弹这一次），成功发起返回 True。

    清单里不写 requireAdministrator：那会让 --restore、查看状态也强制提权，
    而这些操作在便携安装（非 Program Files）上并不需要管理员。
    """
    if os.name != "nt":
        return False
    import ctypes
    exe, argv = launcher()
    params = subprocess.list2cmdline(argv + extra_args)
    try:
        rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, os.getcwd(), 1)
    except Exception:
        return False
    return int(rc or 0) > 32          # >32 才算成功，1223 = 用户取消


# ---------------------------------------------------------------- 备份指纹

def fingerprint(cvi):
    sizes = {}
    for rel in FP_FILES:
        p = os.path.join(cvi, rel.replace("\\", os.sep))
        try:
            sizes[rel] = os.path.getsize(p)
        except OSError:
            sizes[rel] = -1
    return sizes


def meta_path(base):
    return os.path.join(base, "meta.json")


def load_meta(base):
    try:
        with open(meta_path(base), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def save_meta(base, cvi):
    data = {"app": APP, "version": VERSION,
            "installed": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fingerprint": fingerprint(cvi)}
    with open(meta_path(base), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return data


def check_meta(base, cvi):
    """备份是否属于当前这份 CVI。返回告警文本，无异常返回 None。"""
    meta = load_meta(base)
    if not meta or "fingerprint" not in meta:
        return None
    old, now = meta["fingerprint"], fingerprint(cvi)
    if isinstance(old, dict) and "sizes" in old:      # 兼容早期带 header 的格式
        old = old["sizes"]
    if old == now:
        return None
    return ("备份来自另一份 CVI 安装（记录于 %s）。\n"
            "   备份：%s\n"
            "   当前：%s" % (meta.get("installed", "未知时间"), old, now))


def retire_backup(base):
    """把过期备份改名保留，避免旧版本的原始文件覆盖新版本的安装。"""
    backup = os.path.join(base, "backup")
    if not os.path.isdir(backup):
        return None
    dst = os.path.join(base, "backup." + time.strftime("%Y%m%d-%H%M%S"))
    try:
        os.rename(backup, dst)
    except OSError as exc:
        print("   ! 无法移走过期备份（%s），继续使用原目录" % exc)
        return None
    return dst


# ---------------------------------------------------------------- 文件操作

def read_list(base):
    """优先用载荷清单；payload 被删掉时退回遍历 backup。"""
    lst = os.path.join(base, "payload", "_files.txt")
    if os.path.exists(lst):
        return [x.strip().replace("\\", "/")
                for x in read_bytes(lst).decode("ascii", "replace").splitlines() if x.strip()]
    backup = os.path.join(base, "backup")
    out = []
    for dirpath, _, names in os.walk(backup):
        for n in names:
            rel = os.path.relpath(os.path.join(dirpath, n), backup)
            out.append(rel.replace("\\", "/"))
    return sorted(out)


def do_backup(cvi, backup, rels):
    saved = 0
    for rel in rels:
        src = os.path.join(cvi, rel.replace("/", os.sep))
        dst = os.path.join(backup, rel.replace("/", os.sep))
        if not os.path.exists(src) or os.path.exists(dst):
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        # 拷贝中途失败（磁盘满、被拦截）时绝不留下半份备份，否则还原会把文件写坏
        if os.path.getsize(dst) != os.path.getsize(src):
            os.remove(dst)
            raise OSError("备份 %s 时字节数不一致" % rel)
        saved += 1
    return saved


def do_copy(src_root, dst_root, rels):
    """返回 (已写入列表, 失败列表)。失败列表用于回滚。"""
    ok, fail = [], []
    for rel in rels:
        src = os.path.join(src_root, rel.replace("/", os.sep))
        dst = os.path.join(dst_root, rel.replace("/", os.sep))
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            if os.path.getsize(dst) != os.path.getsize(src):
                raise OSError("写入后字节数不一致")
            ok.append(rel)
            print("   [写入] %s" % rel)
        except Exception as e:
            fail.append("%s: %s" % (rel, e))
            print("   [失败] %s  %s" % (rel, e))
    return ok, fail


def rollback(cvi, backup, written):
    """把已经写进去的文件退回原始副本，避免留下中英混杂的安装目录。"""
    back = 0
    for rel in written:
        src = os.path.join(backup, rel.replace("/", os.sep))
        dst = os.path.join(cvi, rel.replace("/", os.sep))
        if not os.path.exists(src):
            continue
        try:
            shutil.copy2(src, dst)
            back += 1
        except Exception as e:
            print("   [回滚失败] %s  %s" % (rel, e))
    return back


# ---------------------------------------------------------------- 主流程

def install(cvi, base):
    try:
        import make_payload          # 只有安装路径需要它（连带 pefile），还原路径不导入
    except ImportError as exc:
        print("\n[中止] 安装程序不完整，缺少依赖：%s" % exc)
        print("       源码运行时请先执行：pip install -r requirements.txt")
        return 3

    if cvi_running():
        print("\n[中止] LabWindows/CVI 正在运行，请先关闭再重试。")
        return 2

    if is_patched(cvi):
        print("\n[提示] 该安装目录已经是汉化状态。")
        print("       如需重装，请先运行：%s --restore" % (os.path.basename(sys.argv[0]) or "本程序"))
        return 1

    warn = check_meta(base, cvi)
    backup = os.path.join(base, "backup")
    if warn:
        print("\n[注意] %s" % warn)
        if os.path.isdir(backup):
            old = retire_backup(base)
            if not old:
                print("\n[中止] 无法移走过期备份，为避免旧文件覆盖新版本，未做任何更改。")
                print("       请手动把 %s 改名后重试。" % backup)
                return 3
            print("       旧备份已改名保留：%s" % old)
        print("       本次将重新备份当前文件。")

    payload = os.path.join(base, "payload")
    print("\n工作目录：%s" % base)

    print("\n[1/3] 生成补丁文件（只读 CVI 安装目录，不写入）")
    try:
        files = make_payload.build(cvi, payload)
    except SystemExit as e:
        print("\n[中止] %s" % e)
        return 3
    if not files:
        print("\n[中止] 没有生成任何补丁文件。")
        return 3

    print("\n[2/3] 备份原始文件")
    try:
        saved = do_backup(cvi, backup, files)
    except OSError as exc:
        print("\n[中止] 备份失败：%s" % exc)
        print("       安装目录未被修改。")
        return 3
    print("   新增备份 %d 个（已存在的备份不覆盖）" % saved)
    if not load_meta(base) or warn:
        save_meta(base, cvi)
        print("   记录安装指纹：%s" % (fingerprint(cvi),))

    print("\n[3/3] 写入安装目录")
    ok, fail = do_copy(payload, cvi, files)
    print("\n成功 %d 个，失败 %d 个" % (len(ok), len(fail)))
    if fail:
        print("\n[回滚] 正在把已写入的文件退回原始版本 ...")
        back = rollback(cvi, backup, ok)
        print("[回滚] 已退回 %d 个文件，安装目录应已恢复英文。" % back)
        print("       失败通常是 CVI 未关闭、文件被占用或没有写入权限。")
        return 4

    print("\n完成。重新打开 LabWindows/CVI 即为中文界面。")
    print("如需还原英文，再次运行本程序并选择还原，或执行：\n  \"%s\" --restore"
          % os.path.abspath(sys.argv[0]))
    return 0


def restore(cvi, base):
    if cvi_running():
        print("\n[中止] LabWindows/CVI 正在运行，请先关闭再重试。")
        return 2

    backup = os.path.join(base, "backup")
    if not os.path.isdir(backup):
        print("\n[中止] 找不到备份目录：%s" % backup)
        print("       没有备份无法还原，只能重装 LabWindows/CVI。")
        return 3

    rels = read_list(base)
    if not rels:
        print("\n[中止] 备份目录是空的。")
        return 3

    warn = check_meta(base, cvi)
    if warn:
        print("\n[注意] %s" % warn)
        print("       把旧备份写回新版本可能导致版本错配。")

    print("\n[1/2] 从 %s 还原 %d 个文件" % (backup, len(rels)))
    ok, fail = do_copy(backup, cvi, rels)
    print("\n[2/2] 成功 %d 个，失败 %d 个" % (len(ok), len(fail)))
    if fail:
        return 4
    print("\n已还原为英文界面。")
    return 0


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--cvi", default=None, help="CVI 安装根目录；省略则自动探测")
    ap.add_argument("--restore", action="store_true", help="还原英文")
    ap.add_argument("--yes", action="store_true", help="不等待按键（脚本调用）")
    ap.add_argument("--version", action="version", version="%(prog)s " + VERSION)
    ap.add_argument("--elevated", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args()

    print("=" * 58)
    print("  LabWindows/CVI 2015 汉化包  %s" % VERSION)
    print("=" * 58)

    try:
        cvi = cviroot.find(a.cvi)
    except SystemExit as e:
        print(e)
        if not a.yes:
            input("\n按回车退出 ...")
        return 1

    print("\n安装目录：%s" % cvi)
    patched = is_patched(cvi)
    print("当前状态：%s" % ("中文" if patched else "英文"))

    # 只在真的写不进去时才提权：便携安装、已提权的终端、非 Program Files 都不打扰用户
    if not can_write(cvi) and not is_admin():
        if a.elevated:
            print("\n[中止] 已请求管理员权限，但仍无法写入该目录。")
            print("       请检查目录只读属性或安全设置。")
            if not a.yes:
                input("\n按回车退出 ...")
            return 5
        print("\n该目录需要管理员权限才能写入，正在请求提权 ...")
        # 提权后的进程在新控制台里跑，本进程随即退出；脚本调用要看结果得等新窗口结束。
        if relaunch_elevated(["--elevated"]):
            return 0
        print("已取消提权，未做任何更改。")
        if not a.yes:
            input("\n按回车退出 ...")
        return 5

    try:
        if a.restore:
            rc = restore(cvi, base_dir())
        elif patched:
            print("\n[提示] 这个安装目录已经是中文，不需要再安装。")
            if not a.yes and ask("       是否还原成英文？[y/N] ") in ("y", "yes"):
                rc = restore(cvi, base_dir())
            else:
                print("       未做任何更改。")
                rc = 1
        else:
            rc = install(cvi, base_dir())
    except SystemExit as e:
        print("\n%s" % e)
        rc = 1
    except Exception as e:
        print("\n[异常] %s: %s" % (type(e).__name__, e))
        rc = 9

    if not a.yes:
        input("\n按回车退出 ...")
    return rc


if __name__ == "__main__":
    sys.exit(main())
