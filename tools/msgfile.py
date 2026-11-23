#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cvimsgs.txt 读写库。

文件格式（CRLF）：
    首行    <条数> <总字节数>
    后续行  <ID><若干空格>"<文本>"

文本内部为 C 风格字面量：\\n \\t \\" 以及相邻字面量拼接的 `" "`。
本模块只做“逐条替换文本”，完整保留 ID、空格填充、引号与转义序列。
"""
import re

LINE_RE = re.compile(r'^(\d+)(\s+)(".*")\s*$')


def emit_literal(text):
    """把内容串还原为 C 字面量写法：在每个 \\n 边界处拆成相邻字面量。"""
    parts = text.split("\\n")
    if len(parts) == 1:
        return '"%s"' % text
    chunks = ['"%s\\n"' % p for p in parts[:-1]]
    chunks.append('"%s"' % parts[-1])
    return " ".join(chunks)


class MsgFile:
    def __init__(self, path):
        self.path = path
        with open(path, "rb") as f:
            raw = f.read()
        self.bom = b""
        if raw.startswith(b"\xef\xbb\xbf"):
            self.bom, raw = raw[:3], raw[3:]
        self.crlf = b"\r\n" in raw
        self.final_nl = raw.endswith(b"\r\n") or raw.endswith(b"\n")
        # CVI 为 ANSI 程序，本机 ACP=936；用 GBK 解码 + surrogateescape 保证字节级往返一致
        text = raw.decode("gbk", errors="surrogateescape")
        lines = text.split("\r\n") if self.crlf else text.split("\n")
        self.header = lines[0]
        self.items = {}          # id -> text (已还原转义前的原始字面量内容)
        self.order = []
        self.prefix = {}         # id -> 原始空格填充
        self.raw = {}            # id -> 原始字面量（未改动时按原样写回）
        self.trailing = []
        for ln in lines[1:]:
            if not ln.strip():
                continue
            m = LINE_RE.match(ln)
            if not m:
                self.trailing.append(ln)
                continue
            i = int(m.group(1))
            if i in self.items:
                # 同一个 ID 出现两次时，写回会产出两行内容不同的条目，
                # CVI 取第一条，肉眼却看到第二条——这里直接报错，逼数据修正。
                raise ValueError("%s: 消息 ID %d 重复" % (path, i))
            # 相邻字面量拼接 `" "` 只是源码换行手段，归一为单一内容串；
            # 保存时再按 \n 边界重新拆分，保持与原文件同构。
            self.items[i] = m.group(3)[1:-1].replace('" "', "")
            self.raw[i] = m.group(3)
            self.prefix[i] = m.group(2)
            self.order.append(i)

    def save(self, path=None):
        path = path or self.path
        out = [self.header]
        for i in self.order:
            lit = self.raw.get(i)
            if lit is None or self.items[i] != lit[1:-1].replace('" "', ""):
                lit = emit_literal(self.items[i])
            out.append("%d%s%s" % (i, self.prefix[i], lit))
        out.extend(self.trailing)
        data = ("\r\n" if self.crlf else "\n").join(out)
        if self.final_nl:
            data += "\r\n" if self.crlf else "\n"
        with open(path, "wb") as f:
            f.write(self.bom + data.encode("gbk", errors="surrogateescape"))


# ---------- 文本层面工具 ----------
def visible(t):
    """把字面量还原为“人看到的文本”，用于判断可读性/长度约束。
    去掉相邻字面量拼接符 `" "`，把 \\n 等还原为控制字符。"""
    s = t.replace('" "', "")
    s = s.replace('\\n', "\n").replace('\\t', "\t").replace('\\"', '"').replace("\\\\", "\\")
    return s


def mnemonic(s):
    """返回 (去掉助记符标记的纯文本, 标记风格)。
    CVI 用 `__X` 或 `&X` 标记助记符。"""
    if "__" in s:
        return s.replace("__", ""), "__"
    if "&" in s:
        return s.replace("&", ""), "&"
    return s, None
