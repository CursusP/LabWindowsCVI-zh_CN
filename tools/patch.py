#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CVI 汉化 · 补丁应用器
--------------------------------------------------
原理：CVI 为 ANSI(MBCS) 程序，界面字符串以 NUL 结尾的 ASCII 字面量存放在 PE 的
      .rdata/.data 段中，运行时按系统代码页(CP936)解释。因此把译文以 GBK 编码
      “原地覆盖”到原字面量槽位即可，无需改动 PE 结构与代码，不触碰功能逻辑。

安全性：
  * 只在 .rdata / .data 段内改写，绝不触碰 .text（代码）
  * 槽位必须左右都是 NUL 边界，避免命中内部标识符（Open / ExplorerOpen）
  * 译文 GBK 字节数必须 <= 原文 ASCII 字节数，否则拒绝该条（记入报告）
  * 槽位剩余字节以 0x00 填充，C 字符串在首个 NUL 处正常结束
用法：
  python patch.py apply   [--src D:\\CVI2015] [--out ..\\out\\patched]
  python patch.py restore [--dir ..\\out\\patched]
  python patch.py verify  [--dir ..\\out\\patched]
"""
import argparse
import datetime
import hashlib
import json
import os
import sys

import pefile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cviroot
import paths

ROOT = paths.ROOT
TM_FILE = os.path.join(ROOT, "tm", "core_entries.json")

# 需要汉化的目标（IDE 主程序与主要工具）
TARGETS = [
    "cvi.exe", "cvi.dll",
    "bin\\fmtwz.exe", "bin\\iconedit.exe", "bin\\uiconv.exe", "bin\\convuir.exe",
    "bin\\localui.exe", "bin\\cvilink.exe", "compile.exe",
]
PATCH_SECS = {".rdata", ".data"}


# 绝不翻译：Win32 窗口类名 / 配置值 / 注册表键（翻译后 CreateWindowEx 会失败）
CLASS_BLACKLIST = {
    "button", "static", "edit", "combobox", "comboboxex32", "listbox", "scrollbar",
    "menu", "dialog", "syslistview32", "toolbarwindow32", "mdiclient", "richedit",
    "control", "controls", "software", "path", "clsid", "mime", "hardware", "interface",
    "component categories", "system64folder", "system16folder", "nishareddir",
}


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def write_bytes(path, data):
    with open(path, "wb") as f:
        f.write(data)


def is_safe_to_patch(src):
    """仅当该串明确是“给人看的短语/标签”时才允许改写。
    单 token（无空格且不以冒号结尾）一律不自动改：它极可能同时是类名/配置值/命令键。"""
    if src.strip().lower() in CLASS_BLACKLIST:
        return False
    if " " not in src and not src.rstrip().endswith(":"):
        return False
    return True


def load_tm():
    """读取译文表，返回带长度信息的条目列表。

    源串必须是 ASCII、译文必须能编码为 GBK；任一不满足说明 tm/ 有数据错误，
    这里直接中止并指出具体条目，而不是抛出未处理的 traceback。
    """
    with open(TM_FILE, encoding="utf-8") as f:
        data = json.load(f)
    items = []
    for e in data["entries"]:
        if e.get("action") != "translate":
            continue
        src, zh = e["src"], e.get("zh", "")
        if not is_safe_to_patch(src):
            continue
        if not zh or zh == src:
            continue
        try:
            src_b = len(src.encode("ascii", "strict"))
            zh_b = len(zh.encode("gbk", "strict"))
        except UnicodeEncodeError as exc:
            raise SystemExit(
                "!! 译文表编码错误：%r -> %r（%s）\n"
                "   原文必须为 ASCII，译文必须能编码为 GBK。" % (src, zh, exc)
            )
        items.append({"src": src, "zh": zh, "cat": e.get("cat", ""),
                      "src_b": src_b, "zh_b": zh_b})
    return items


def section_spans(pe):
    """返回 {段名: (文件偏移, 原始大小)}"""
    out = {}
    for s in pe.sections:
        nm = s.Name.rstrip(b"\x00").decode("latin1")
        out[nm] = (s.PointerToRawData, s.SizeOfRawData)
    return out


def build_index(needles):
    """把待查字面量按首字节分组。

    逐条正则要扫 169 遍全文；按首字节分组后每个首字节只扫一遍（约 40 组），
    实测同一文件 0.93s -> 0.35s。反过来用一条交替式正则会更慢（5.6s），别试。
    """
    index = {}
    for nb in needles:
        index.setdefault(nb[0], []).append(nb)
    return index


def scan_literals(buf, index, start, end):
    """一趟扫出所有左右都是 NUL 边界的字面量，返回 {字面量: [位置...]}。

    必须左右都是 NUL 边界：否则 "Show at Startup" 会命中 "__Show at Startup"，
    "Open" 会命中 "ExplorerOpen"，翻译后破坏内部标识符与函数名。
    """
    found = {}
    end = min(end, len(buf))
    for first, needles in index.items():
        pos = start
        while True:
            i = buf.find(first, pos, end)
            if i < 0:
                break
            if i == start or buf[i - 1] == 0:
                for nb in needles:
                    j = i + len(nb)
                    if j < end and buf[j] == 0 and buf.startswith(nb, i):
                        found.setdefault(nb, []).append(i)
            pos = i + 1
    return found


def guard_pristine(src_root, tm, sentinels=12):
    """防止在已汉化的文件上二次抽取：源里只要出现译文字面量就中止。

    v1.0 时这里扫全表（169 条 × 26 MB），一次 1.5 秒且随词条线性增长。
    现在只取最长的若干条译文当哨兵：真实汉化过一遍的文件必然命中其中数条，
    12 条 × 26 MB 的查找约 50 毫秒。文本通道另由 check_pristine() 精确校验，
    二进制通道即使漏判，补丁也只是在英文槽位上重写一次，不会破坏文件。
    """
    sent = []
    for it in sorted(tm, key=lambda x: -x["zh_b"]):
        if it["zh_b"] > it["src_b"] or it["zh_b"] < 6:
            continue
        sent.append((b"\x00" + it["zh"].encode("gbk") + b"\x00", it["src"]))
        if len(sent) >= sentinels:
            break
    if not sent:
        print("   ! 没有可用的哨兵串，跳过纯净性抽检")
        return

    hits = 0
    examples = []
    for rel in TARGETS:
        p = os.path.join(src_root, rel)
        if not os.path.exists(p):
            continue
        buf = read_bytes(p)
        for needle, src in sent:
            if needle in buf:
                hits += 1
                if len(examples) < 5:
                    examples.append((rel, src))
    # 单条命中可能是二进制里的巧合字节序列，≥2 条即可判定为已汉化
    if hits >= min(2, len(sent)):
        print("!! 源目录已包含汉化字节，请在原始安装上运行，或先运行 restore.bat 还原：")
        for rel, src in examples:
            print("   %s  ←  %s" % (rel, src))
        sys.exit(2)


def cmd_apply(args):
    tm = load_tm()
    src_root = cviroot.find(args.src)
    out_root = args.out
    guard_pristine(src_root, tm)
    os.makedirs(out_root, exist_ok=True)

    manifest = {"created": datetime.datetime.now().isoformat(timespec="seconds"),
                # 只记录目录名，避免把本机绝对路径写进会随发布包分发的清单
                "source_root": os.path.basename(os.path.normpath(os.path.abspath(src_root))),
                "files": [], "overflow": []}
    total_patched = 0
    index = build_index([it["src"].encode("ascii") for it in tm])
    missing = []

    for rel in TARGETS:
        src_path = os.path.join(src_root, rel)
        if not os.path.exists(src_path):
            missing.append(rel)
            continue
        dst_path = os.path.join(out_root, rel)
        parent = os.path.dirname(dst_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        try:
            pe = pefile.PE(src_path, fast_load=True)
        except pefile.PEFormatError as exc:
            raise SystemExit("!! 不是有效的 PE 文件：%s（%s）" % (src_path, exc))
        try:
            spans = section_spans(pe)
        finally:
            pe.close()

        orig = read_bytes(src_path)
        buf = bytearray(orig)
        file_rec = {"file": rel, "patches": [], "hits": {}}

        # 先在不可变的原始字节上把整段扫完，再统一写入。
        # 旧写法每条词目都对 buf 做一次 bytes() 复制（18 MB × 169 次），
        # 既慢又会在已改写的字节上做后续匹配。
        slots = {}
        for sec, (off, sz) in spans.items():
            if sec not in PATCH_SECS:
                continue
            for nb, positions in scan_literals(orig, index, off, off + sz).items():
                slots.setdefault(nb, []).extend((sec, p) for p in positions)

        for it in tm:
            hits = slots.get(it["src"].encode("ascii")) or []
            if not hits:
                continue
            if it["zh_b"] > it["src_b"]:
                manifest["overflow"].append(
                    {"file": rel, "src": it["src"], "zh": it["zh"],
                     "need": it["zh_b"], "have": it["src_b"]})
                continue
            zh_b = it["zh"].encode("gbk")
            for sec, pos in hits:
                # 理论上不会发生：槽位来自同一份字节，越界说明 manifest 或扫描有误
                if pos + it["src_b"] + 1 > len(buf):
                    raise SystemExit("!! 内部错误：补丁位置越界 %s @%d" % (rel, pos))
                old = orig[pos:pos + it["src_b"]]
                buf[pos:pos + len(zh_b)] = zh_b
                buf[pos + len(zh_b):pos + it["src_b"] + 1] = \
                    b"\x00" * (it["src_b"] + 1 - len(zh_b))
                file_rec["patches"].append({
                    "src": it["src"], "zh": it["zh"], "cat": it["cat"],
                    "sec": sec, "off": pos, "old": old.decode("ascii"), "len": it["src_b"],
                })
            file_rec["hits"][it["src"]] = len(hits)
            total_patched += len(hits)

        # 没有任何替换的文件不写入载荷：安装清单按 _files.txt 逐项复制，
        # 多出来的副本只会让 payload 目录与实际安装内容对不上。
        if file_rec["patches"]:
            write_bytes(dst_path, bytes(buf))
            file_rec["sha_src"] = hashlib.sha256(orig).hexdigest()[:16]
            file_rec["sha_dst"] = hashlib.sha256(bytes(buf)).hexdigest()[:16]
            manifest["files"].append(file_rec)

    mf = os.path.join(out_root, "_manifest.json")
    with open(mf, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    print("已处理文件 %d 个，替换 %d 处" % (len(manifest["files"]), total_patched))
    if missing:
        print("! 未找到 %d 个目标文件：%s" % (len(missing), ", ".join(missing)))
        print("  版本不一致或安装不完整时会出现这种情况，相关条目不会生效。")
    print("长度超限 %d 条" % len(manifest["overflow"]))
    for o in manifest["overflow"][:20]:
        print("  ! %r -> %r 需%d字节/仅有%d" % (o["src"], o["zh"], o["need"], o["have"]))
    print("manifest: %s" % mf)


def _load_manifest(d):
    mf = os.path.join(d, "_manifest.json")
    if not os.path.exists(mf):
        raise SystemExit("!! 找不到 %s；请先执行 apply 生成补丁" % mf)
    try:
        with open(mf, encoding="utf-8") as f:
            return json.load(f)
    except ValueError as exc:
        raise SystemExit("!! %s 不是合法的 JSON：%s" % (mf, exc))


def cmd_verify(args):
    d = args.dir
    manifest = _load_manifest(d)
    bad = 0
    for f in manifest["files"]:
        p = os.path.join(d, f["file"])
        if not os.path.exists(p):
            bad += len(f["patches"])
            print("  ! 缺少文件 %s" % f["file"])
            continue
        buf = read_bytes(p)
        for pa in f["patches"]:
            end = pa["off"] + pa["len"]
            if end > len(buf):
                bad += 1
                print("  ! %s @%d: 偏移越界" % (f["file"], pa["off"]))
                continue
            seg = buf[pa["off"]:end]
            try:
                txt = seg.split(b"\x00")[0].decode("gbk")
            except UnicodeDecodeError:
                txt = "<解码失败>"
            if txt != pa["zh"]:
                bad += 1
                print("  ! %s @%d: 期望 %r 实际 %r" % (f["file"], pa["off"], pa["zh"], txt))
    tot = sum(len(f["patches"]) for f in manifest["files"])
    print("校验：共 %d 处补丁，异常 %d 处。%s" % (tot, bad, "通过" if bad == 0 else "未通过"))
    return 0 if bad == 0 else 1


def cmd_restore(args):
    d = args.dir
    manifest = _load_manifest(d)
    restored = 0
    for f in manifest["files"]:
        p = os.path.join(d, f["file"])
        if not os.path.exists(p):
            print("  ! 跳过（文件不存在）：%s" % f["file"])
            continue
        buf = bytearray(read_bytes(p))
        for pa in f["patches"]:
            old = pa["old"].encode("ascii")
            end = pa["off"] + pa["len"] + 1
            # manifest 被截断或来自另一份文件时，宁可报错也不写坏文件
            if len(old) != pa["len"] or end > len(buf):
                raise SystemExit("!! manifest 与 %s 不匹配（偏移 %d）" % (f["file"], pa["off"]))
            buf[pa["off"]:end] = old + b"\x00"
        write_bytes(p, bytes(buf))
        restored += 1
    print("已按 manifest 还原 %s 中的 %d 个文件" % (d, restored))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="在 PE 的 .rdata/.data 段内原地覆盖中文字符串")
    ap.add_argument("cmd", choices=["apply", "verify", "restore"])
    ap.add_argument("--src", default=None, help="CVI 安装根目录；省略则自动探测")
    ap.add_argument("--out", default=os.path.join(ROOT, "out", "patched"))
    ap.add_argument("--dir", default=os.path.join(ROOT, "out", "patched"))
    a = ap.parse_args()
    sys.exit({"apply": cmd_apply, "verify": cmd_verify, "restore": cmd_restore}[a.cmd](a) or 0)
