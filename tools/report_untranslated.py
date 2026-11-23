"""列出仍未翻译的条目，并按“是否应当翻译”分类。

产出 docs/UNTRANSLATED.md，作为“无遗漏”核查依据：
每条未译项都给出判定理由，便于复核。
"""
import os, re, sys, glob, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from msgfile import MsgFile
import cviroot

TM = os.path.join(ROOT, 'tm')

RULES = [
    ('纯格式字符串', lambda s: not re.search(r'[A-Za-z]{2,}', re.sub(r'%[-+ 0#]*[0-9.]*[hlLqjztI]*[diouxXeEfgGaAcspnVTSm]', '', s))),
    ('文件扩展名或通配符', lambda s: re.fullmatch(r'[\*\.\w?]+\.[A-Za-z0-9]{1,5}', s.strip()) or re.fullmatch(r'\*\.\w+', s.strip())),
    ('C 类型名或关键字', lambda s: re.fullmatch(r'(unsigned |signed )?(char|int|short|long|float|double|void)( \*|\[\d*\])*', s.strip()) or s.strip() in ('__cdecl', '__stdcall', 'int64', 'unsigned int64')),
    ('键盘按键名', lambda s: s.strip() in ('Shift', 'Ctrl', 'Enter', 'Esc', 'Tab', 'Home', 'End', 'Del', 'Ins',
                                          'BkSp', 'Space', 'PgUp', 'PgDown', 'Clear', 'Break', 'Up', 'Down',
                                          'Left', 'Right', 'Help', 'PopupMenu') or re.fullmatch(r'F\d{1,2}', s.strip())),
    ('字符集名称', lambda s: s.strip() in ('Native', 'Western', 'Symbol', 'Shift JIS', 'Hangul', 'GB2312', 'Big5',
                                          'Johab', 'Hebrew', 'Arabic', 'Greek', 'Turkish', 'Vietnamese', 'Thai',
                                          'Eastern European', 'Russian', 'Mac', 'Baltic', 'OEM')),
    ('安装位置令牌', lambda s: re.fullmatch(r'\[[^\]]+\]', s.strip()) is not None),
    ('注册表值类型', lambda s: s.strip() in ('REG_SZ', 'REG_DWORD', 'REG_BINARY', 'REG_EXPAND_SZ')),
    ('示例代码片段', lambda s: ('{' in s and '}' in s) or s.lstrip().startswith(('#', '/*', '//', 'typedef', 'struct', 'int ', 'void ', 'char ', 'extern ', 'static ', 'register ', 'const ', 'float ', 'long ', 'unsigned '))),
    ('UIR 内部类型标识符', lambda s: re.fullmatch(r'[A-Z][A-Za-z]+', s.strip()) is not None),
    ('文件扩展名', lambda s: re.fullmatch(r'\.[A-Za-z0-9]{1,6}', s.strip()) is not None),
    ('内部按键常量名', lambda s: re.fullmatch(r'vk[A-Za-z0-9]+', s.strip()) is not None),
    ('内部文件名', lambda s: re.fullmatch(r'(_files|<cviincludes\.h>|default\.ico|stub\d*\.cvi|html)', s.strip()) is not None),
    ('产品名或缩写', lambda s: s.strip() in ('LabWindows/CVI', 'Unicode', 'type lib fp')),
    ('拼接片段', lambda s: s.strip() in ('of',)),
    ('示例代码片段', lambda s: s.lstrip().startswith('__attribute__') or re.fullmatch(r'\w+\(\);?\s*', s) is not None),
    ('调试输出格式串', lambda s: s.lstrip().startswith(('%c', 'Top T', 'File: %s')) or re.fullmatch(r'[\s%0-9.\-a-zA-Z]*', s) is not None and '%' in s),
    ('内部资源标识', lambda s: s.strip() in ('.NETControllerFinishDialogMetaFont', 'Ctrl-Alt-SysRequest', 'Ctrl+', 'Shift+', 'Caps+', 'MenuKey (Cmd)', 'MenuKey (Meta)', 'MenuKey (Ctrl)', 'short int', 'intptr_t')),
    ('常量名或标记', lambda s: s.strip().startswith('VAL_') or re.fullmatch(r'[A-Za-z_]{1,3}', s.strip()) is not None),
]


def classify(s):
    for name, fn in RULES:
        try:
            if fn(s):
                return name
        except Exception:
            pass
    return '未分类（需人工确认）'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=None, help="英文原版 cvimsgs.txt；省略则自动查找")
    a = ap.parse_args()
    m = MsgFile(cviroot.find_cvimsgs(a.src))
    done = set()
    for f in glob.glob(os.path.join(TM, '*.tsv')):
        with open(f, encoding='utf-8-sig') as fh:
            for ln in fh:
                ln = ln.rstrip('\r\n')
                if '\t' not in ln:
                    continue
                k = ln.split('\t')[0].strip()
                if k.isdigit():
                    done.add(int(k))

    def has_en(s):
        return any('a' <= c.lower() <= 'z' for c in s)

    rest = [(i, m.items[i]) for i in sorted(m.items) if i not in done and has_en(m.items[i])]
    groups = {}
    for i, t in rest:
        groups.setdefault(classify(t), []).append((i, t))

    total = len(m.items)
    lines = [
        '# 未翻译条目清单与判定',
        '',
        f'- `cvimsgs.txt` 总条目：{total}',
        f'- 已翻译：{len(done)}（{len(done) / total * 100:.1f}%）',
        f'- 未翻译且含英文字母：{len(rest)}',
        '',
        '下列条目**按设计保留英文**，逐条给出判定理由。任何一条判错都可以直接在 `tm/*.tsv` 中补一行译文再重新生成。',
        '',
    ]
    order = list(dict.fromkeys([n for n, _ in RULES] + ['未分类（需人工确认）']))
    for name in order:
        items = groups.get(name)
        if not items:
            continue
        lines.append(f'## {name}（{len(items)} 条）')
        lines.append('')
        lines.append('| ID | 原文 |')
        lines.append('|---|---|')
        for i, t in items[:40]:
            cell = t.replace('|', '\\|').replace('\n', ' ')[:90]
            lines.append(f'| {i} | {cell} |')
        if len(items) > 40:
            lines.append(f'| … | 其余 {len(items) - 40} 条同类 |')
        lines.append('')

    out = os.path.join(ROOT, 'docs', 'UNTRANSLATED.md')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(lines))
    print(f"未译 {len(rest)} 条，已写入 {os.path.abspath(out)}")
    for name in order:
        if name in groups:
            print(f"  {name}: {len(groups[name])}")


if __name__ == '__main__':
    main()
