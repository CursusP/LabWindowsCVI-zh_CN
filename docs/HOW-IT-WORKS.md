# 工作原理

本文说明补丁的工作方式与约束条件。安装步骤见 [README](../README.md)。

## 一、CVI 2015 的文本通道

CVI 2015 是 **ANSI/MBCS** 程序：只导入 `CreateWindowExA` / `SetWindowTextA` / `CreateFontA`，
没有 `RT_STRING`、没有 `RT_MENU` 资源，也没有 Unicode 版本。它的界面文本只有两条通道：

### 1. `bin\cvimsgs.txt` —— 运行时消息目录

```
8586 262081
1200	"OK"
1201	"Yes"
...
```

首行是 `<条数> <字节数>`，其后每行 `ID<TAB>"文本"`。菜单栏、菜单命令、对话框标签、按钮、
错误消息、状态栏几乎全在这里（8586 条）。多行消息写成多个相邻字面量：`"a\n" "b"`。

### 2. 各 exe/dll 的 `.rdata` —— NUL 结尾的 ASCII 字面量

窗口标题、工具名、少量对话框标题直接以 C 字符串常量存在 PE 的只读数据段里。共 169 处，分布在 8 个文件。

### 3. 欢迎页

`WelcomePage\welcome.ini` 存标题与按钮文字（22 条），`welcome_page.dll` 里存额外一条
`Show at Startup`（同时是 `StartupCheckStr` 的值与复选框文字）。

## 二、为什么是「原地覆盖」

GBK 是双字节变长编码，中文信息密度高于英文，绝大多数条目的 GBK 字节数不超过原文 ASCII 字节数。
于是最省事、也最不容易破坏程序的做法是：**在原字面量槽位写入 GBK 字节，剩余空间补 `\x00`**。

- 不改 PE 结构、不改节表、不改代码段；
- 字符串仍在原地址，所有引用它的代码无需重定位；
- C 字符串在首个 `\x00` 处自然结束，槽位剩余字节被忽略。

唯一的硬约束：`len(译文GBK) ≤ len(原文ASCII)`。超长条目会被 `msgpatch.py` / `patch.py`
**拒绝并记入报告**，而不是截断——截断会写出半个汉字，产生乱码。

## 三、四个必须知道的坑

| 坑 | 后果 | 本仓库的处理 |
|---|---|---|
| 改完 `cvimsgs.txt` 不重算首行 | 加载器校验失败，**静默回退英文**，看着像「汉化无效」 | `msgpatch.py` 每次调用官方 `countmsg.exe` 重算 |
| 把 `Button` / `Edit` / `Static` 等窗口类名一起翻译 | 主窗口创建不出来（进程活着但没窗口） | 单 token 不自动改写 + 类名/注册表键黑名单 |
| 按英文词精确搜索 | 助记符 `__` 会插进单词（`Threads` 实为 `T__hreads`），搜不到就误判「不存在」 | 检索时同时尝试 `__X` 变体 |
| 多行消息是多个字面量拼接 | 直接改会破坏 `"a\n" "b"` 结构 | 解析时归一、写回时按 `\n` 边界重建；未改动的行按原字节写回 |

另有一条经验：**不要在已汉化的文件上二次加工**。`make_payload.py` 会检查 `cvimsgs.txt` 是否含
非 ASCII 字节（精确）；`patch.py` 则用最长的一批译文当哨兵，在目标二进制里搜到两条以上就中止。
哨兵是抽样，但配合文本通道的精确检查已足够——即便漏判，补丁也只是在英文槽位上重写一次，
不会把已汉化的文件改坏。

## 四、字符串槽位必须左右都是 NUL

`patch.py` 用「`needle + \x00` 且左侧为 `\x00` 或段首」来定位槽位（`scan_literals`）。
早期只匹配右边界，结果 `Open` 命中了 `ExplorerOpen`、`Project` 命中了 `NewEmptyProject`、
`MenuIsOpen` 也被改坏——一次改坏 5 处。左右边界同时校验后，命中数与译文表严格一一对应。

这类误伤在编译期、运行期都不报错，只会让某个菜单项变成乱码或被截断，所以宁可少改不可多改。

## 五、编码与区域设置

- 文件按 **GBK（CP936）字节**写入，`.tsv` 源文件用 UTF-8-SIG 保存，便于 Excel 直接打开不乱码。
- 运行环境必须是中文(GBK/936)。Windows 的「Beta: 使用 Unicode UTF-8」会把系统 ACP 改成 65001，
  GBK 字节被按 UTF-8 解释，界面会整片乱码。
- `.bat` 自身也以 GBK 编码保存并强制 CRLF，否则中文提示在不同代码页下会变成乱码。

## 六、可复现的校验链路

```bat
python tools\lint_tm.py          :: 译文表自身：格式、重复 ID、编码、引号
python tools\tmcheck.py          :: 与英文原文比对：格式说明符序列、\n 数量
python tools\msgpatch.py apply   :: 应用 → countmsg 重算头部 → 回读校验
python tools\msgpatch.py verify  :: 校验产出文件与译文表一致
python tools\patch.py verify --dir payload
```

前三步的失败都是「拒绝写入」而不是「写坏」，因此可以放心在 CI 里跑 `lint_tm.py`。

## 七、运行环境与 Windows 7

补丁本身只是字节替换，没有额外的系统依赖；限制来自安装程序的打包方式：

- 单文件安装程序用 CPython 3.8.10 打包。CPython 3.9 起不再支持 Windows 7，
  因此 3.8 是能同时覆盖 Windows 7 SP1 与 Windows 10/11 的最后一个版本。
- 安装程序为 64 位 PE，Windows 7 需 SP1 且已安装 KB2533623
  （该更新向 `kernel32.dll` 补充 `AddDllDirectory`，较新的累积更新通常已包含）。
- Visual C++ 运行库随包分发，目标机无需另行安装。
- 32 位系统或未安装上述更新的 Windows 7 可使用批处理方式；
  `python38.dll` 不依赖 `AddDllDirectory`，只要求本机 Python 3.8 及以上。
