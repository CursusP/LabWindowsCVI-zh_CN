# 未翻译条目清单与判定

- `cvimsgs.txt` 总条目：8586
- 已翻译：8184（95.3%）
- 未翻译且含英文字母：373

下列条目**按设计保留英文**，逐条给出判定理由。任何一条判错都可以直接在 `tm/*.tsv` 中补一行译文再重新生成。

## 纯格式字符串（61 条）

| ID | 原文 |
|---|---|
| 507 | t |
| 508 | S |
| 509 | I |
| 514 | O |
| 2170 | /*  *\\  \r\n/\r\n*/ |
| 4009 | %6lu    %08p    %8Iu    |
| 4010 |  %02lx |
| 5000 | %s %s%s%s%s |
| 6001 | .c |
| 6002 | .a |
| 6003 | .o |
| 6008 | .h |
| 6244 | F1 |
| 6245 | F2 |
| 6246 | F3 |
| 6247 | F4 |
| 6248 | F5 |
| 6249 | F6 |
| 6250 | F7 |
| 6251 | F8 |
| 6252 | F9 |
| 6253 | F10 |
| 6254 | F11 |
| 6255 | F12 |
| 6264 | M+ |
| 6968 | X |
| 8261 | %s |
| 8352 | \"%s\" |
| 8354 | %s |
| 9186 | %s |
| 12833 | \"%s\" |
| 13245 | 0x%08p  |
| 13602 | %m/%d/%y |
| 13603 | %H:%M:%S |
| 13604 | %b %d %H:%M:%S %Y |
| 17000 | %s |
| 17198 | 0 B |
| 18142 | %s\n%s |
| 18150 | %s |
| 18151 | %s |
| … | 其余 21 条同类 |

## 文件扩展名或通配符（9 条）

| ID | 原文 |
|---|---|
| 9192 | cvidebug.dll |
| 9193 | cvidebug.386 |
| 9194 | cvidev.dll |
| 9241 | cvi.hlp |
| 10523 | *.fp |
| 13723 | default.ico |
| 13746 | stub2.cvi |
| 13747 | stub16.cvi |
| 13748 | stub.cvi |

## C 类型名或关键字（11 条）

| ID | 原文 |
|---|---|
| 2878 | __cdecl |
| 2879 | __stdcall |
| 2887 | unsigned char[8] |
| 6895 | int |
| 6896 | unsigned int |
| 6897 | double |
| 6898 | float |
| 6901 | char |
| 6902 | unsigned char |
| 6903 | int64 |
| 6904 | unsigned int64 |

## 键盘按键名（27 条）

| ID | 原文 |
|---|---|
| 1040 | Tab |
| 6202 | Ctrl |
| 6205 | Shift |
| 6230 | Clear |
| 6231 | Enter |
| 6232 | Break |
| 6233 | Up |
| 6234 | Down |
| 6235 | Left |
| 6236 | Right |
| 6237 | Ins |
| 6238 | Del |
| 6239 | Home |
| 6240 | End |
| 6241 | PgUp |
| 6242 | PgDown |
| 6243 | Help |
| 6257 | Esc |
| 6258 | Tab |
| 6259 | Del |
| 6260 | BkSp |
| 6261 | Space |
| 6262 | PopupMenu |
| 7099 | Shift |
| 7100 | Ctrl |
| 7105 | Enter |
| 7106 | Esc |

## 字符集名称（19 条）

| ID | 原文 |
|---|---|
| 6850 | Native |
| 6851 | Western |
| 6852 | Symbol |
| 6853 | Shift JIS |
| 6854 | Hangul |
| 6855 | GB2312 |
| 6856 | Big5 |
| 6857 | Johab |
| 6858 | Hebrew |
| 6859 | Arabic |
| 6860 | Greek |
| 6861 | Turkish |
| 6862 | Vietnamese |
| 6863 | Thai |
| 6864 | Eastern European |
| 6865 | Russian |
| 6866 | Mac |
| 6867 | Baltic |
| 6868 | OEM |

## 安装位置令牌（31 条）

| ID | 原文 |
|---|---|
| 17158 | [Desktop] |
| 17159 | [Windows Volume] |
| 17160 | [Program Files] |
| 17161 | [Program Files (x86)] |
| 17162 | [Windows] |
| 17163 | [System] |
| 17164 | [SysWOW64] |
| 17165 | [System16] |
| 17166 | [Common Files] |
| 17167 | [Common Files (x86)] |
| 17168 | [Global Assembly Cache] |
| 17169 | [Start>>Programs] |
| 17170 | [Startup] |
| 17171 | [Start Menu] |
| 17172 | [Temp] |
| 17173 | [Favorites] |
| 17174 | [Fonts] |
| 17175 | [Templates] |
| 17176 | [Send To] |
| 17177 | [National Instruments] |
| 17178 | [National Instruments (x86)] |
| 17179 | [LabVIEW] |
| 17180 | [CVI] |
| 17181 | [CVI Shared] |
| 17182 | [CVI Public Documents] |
| 17183 | [IVI Std Root] |
| 17184 | [VXI PnP] |
| 17185 | [Inf Store] |
| 17186 | [VXI PnP OS] |
| 17187 | [Program Data] |
| 17188 | [Public Documents] |

## 注册表值类型（4 条）

| ID | 原文 |
|---|---|
| 17217 | REG_EXPAND_SZ |
| 17218 | REG_DWORD |
| 17219 | REG_BINARY |
| 17220 | REG_SZ |

## 示例代码片段（51 条）

| ID | 原文 |
|---|---|
| 1912 | int foo() { }  |
| 1924 | float foo[2][1] = { 1, 3, 5, }; |
| 1948 | static int foo(); |
| 1954 | void foo(int bar) { } |
| 1987 | __attribute__ ((foo)) void bar(); |
| 2005 | foo();  |
| 2020 | char *foo = \"?\?-\"; |
| 2023 | char foo = 'bar'; |
| 2026 | long long foo(); |
| 2029 | #pragma unknown_pragma |
| 2032 | #pragma options align=bit_packed  |
| 2035 | #pragma options align=reset |
| 2038 | #pragma STDC CX_LIMITED_RANGE foo |
| 2041 | #pragma unused(foo,) |
| 2044 | #pragma STDC CX_LIMITED_RANGE ON FOO |
| 2047 | #pragma STDC FENV_ACCESS ON |
| 2050 | #pragma GCC diagnostic error \"-Wdivision-by-zero\" 101 |
| 2053 | char foo = '1234'; |
| 2062 | #define FOO(...)  { } |
| 2065 | #define foo[a,b] |
| 2074 | #define __LINE__ foo |
| 2077 | #undef __LINE__ |
| 2080 | #define foo \"bar\" |
| 2089 | char foo = 'bar'; |
| 2107 | #include_next<ansi_c.h> |
| 2110 | #ifdef foo,\r\n#endif |
| 2113 | #line 011 |
| 2116 | __attribute__ ((__weak_import__)) int foo; |
| 2128 | float foo = 0xFp100000000000000000000; |
| 2131 | const char *foo = \"abc \\m def\"; |
| 2137 | char foo[2] = \"bar\"; |
| 2140 | char foo[2] = {{{1}}}; |
| 2146 | const char foo[]; |
| 2158 | float foo[2][1] = { 1, 3, 5, };  |
| 2161 | const char *foo = \"abc; |
| 2164 | register void foo(int bar); |
| 2179 | extern int foo = 3; |
| 2182 | int foo = 0 \|\| 3; |
| 2188 | #include <userint.h>\r\n\r\nCVIFUNC IReports_SetProperty (unsigned int propertyID, unsigne |
| 2242 | int x; |
| … | 其余 11 条同类 |

## UIR 内部类型标识符（65 条）

| ID | 原文 |
|---|---|
| 1000 | ToggleButton |
| 1001 | RadioButton |
| 1002 | CheckBox |
| 1003 | PictureButton |
| 1004 | CommandButton |
| 1005 | BinarySwitch |
| 1006 | LED |
| 1007 | TextBox |
| 1008 | String |
| 1009 | TextMsg |
| 1010 | Ring |
| 1011 | ListBox |
| 1012 | Numeric |
| 1013 | ColorNum |
| 1014 | NumericGauge |
| 1015 | NumericMeter |
| 1016 | NumericTank |
| 1017 | NumericTherm |
| 1018 | NumericKnob |
| 1019 | NumericDial |
| 1020 | NumericSlide |
| 1021 | RingGauge |
| 1022 | RingMeter |
| 1023 | RingTank |
| 1024 | RingTherm |
| 1025 | RingKnob |
| 1026 | RingDial |
| 1027 | RingSlide |
| 1028 | PictureRing |
| 1029 | Decoration |
| 1030 | Graph |
| 1031 | DigGraph |
| 1032 | StripChart |
| 1033 | Picture |
| 1034 | Timer |
| 1035 | Canvas |
| 1036 | Table |
| 1037 | ActiveX |
| 1038 | Tree |
| 1039 | Splitter |
| … | 其余 25 条同类 |

## 文件扩展名（20 条）

| ID | 原文 |
|---|---|
| 4290 | .odl |
| 4293 | .def |
| 5617 | .rtf |
| 5620 | .hlp |
| 5622 | .html |
| 6004 | .lib |
| 6005 | .obj |
| 6006 | .nidobj |
| 6007 | .dll |
| 6009 | .fp |
| 6010 | .uir |
| 6011 | .prj |
| 6012 | .cws |
| 6013 | .cds |
| 6014 | .txt |
| 6015 | .txt |
| 6016 | .bin |
| 6017 | .txt |
| 13259 | .idl |
| 13260 | .axs |

## 内部按键常量名（24 条）

| ID | 原文 |
|---|---|
| 6206 | vkCtrlAltSysRequest |
| 6207 | vkBreak |
| 6208 | vkPopupMenu |
| 6209 | vkDown |
| 6210 | vkEnd |
| 6211 | vkF1 |
| 6212 | vkF10 |
| 6213 | vkF11 |
| 6214 | vkF12 |
| 6215 | vkF2 |
| 6216 | vkF3 |
| 6217 | vkF4 |
| 6218 | vkF5 |
| 6219 | vkF6 |
| 6220 | vkF7 |
| 6221 | vkF8 |
| 6222 | vkF9 |
| 6223 | vkHome |
| 6224 | vkInsert |
| 6225 | vkLeft |
| 6226 | vkPageDown |
| 6227 | vkPageUp |
| 6228 | vkRight |
| 6229 | vkUp |

## 内部文件名（4 条）

| ID | 原文 |
|---|---|
| 1776 | <cviincludes.h> |
| 5621 | html |
| 5623 | _files |
| 13806 | html |

## 产品名或缩写（2 条）

| ID | 原文 |
|---|---|
| 2625 | type lib fp |
| 4535 | LabWindows/CVI |

## 拼接片段（1 条）

| ID | 原文 |
|---|---|
| 1402 | of |

## 调试输出格式串（5 条）

| ID | 原文 |
|---|---|
| 18172 | Top T  Top %%  Cum %%  Tot T  Tot %%  Function |
| 18173 | File: %s\nTot T  Tot %%  Line  Text |
| 18245 | %c %-5u   at %-20p   %s%s |
| 18246 | %c %-5u   at %-20p   %-25s%s (pool func %u) |
| 18259 | %c %p %-20s %s (thread %u) (notify %u) |

## 内部资源标识（10 条）

| ID | 原文 |
|---|---|
| 6256 | Ctrl-Alt-SysRequest |
| 6265 | Ctrl+ |
| 6266 | Shift+ |
| 6267 | Caps+ |
| 6899 | short int |
| 6905 | intptr_t |
| 7101 | MenuKey (Cmd) |
| 7102 | MenuKey (Meta) |
| 7103 | MenuKey (Ctrl) |
| 13378 | .NETControllerFinishDialogMetaFont |

## 常量名或标记（29 条）

| ID | 原文 |
|---|---|
| 1319 | VAL_GRID |
| 1320 | VAL_COLUMN |
| 1321 | VAL_ROW |
| 4191 | mak |
| 4192 | def |
| 4288 | odl |
| 4291 | def |
| 5575 | doc |
| 5616 | rtf |
| 5618 | hpj |
| 5619 | whh |
| 13700 | exe |
| 13701 | ico |
| 13794 | com |
| 13795 | pif |
| 13796 | lnk |
| 13797 | bat |
| 13798 | cmd |
| 13799 | hlp |
| 13800 | txt |
| 13801 | doc |
| 13802 | wri |
| 13803 | xls |
| 13804 | ppt |
| 13805 | htm |
| 13807 | vsd |
| 13808 | xml |
| 13809 | pdf |
| 13810 | reg |
