# LabWindows/CVI 2015 简体中文语言包

本项目为 National Instruments LabWindows/CVI 2015 提供非官方的简体中文界面补丁。
补丁在用户本机生成：仓库与发布包均不包含 National Instruments 的任何二进制文件，
安装时由安装程序读取本机已有的 CVI 安装副本，生成中文文件并写回。

修改仅涉及界面文本，不改变编译流程、调试行为、生成代码与工程文件格式。
需要恢复英文界面时，可使用安装程序的还原功能。

## 1. 项目用途与范围

- 将 CVI 集成开发环境的菜单、对话框、按钮、状态提示、编译与链接诊断、
  调试器信息及运行时错误信息显示为简体中文。
- 保持原有二进制结构：不修改 PE 节表、不修改代码段，仅替换只读数据段中的
  以 NUL 结尾的字符串字面量，以及运行时消息目录 `bin\cvimsgs.txt`。
- 帮助文档（`*.chm`）不在范围内，不翻译、不安装、不分发；安装后帮助仍为英文。

汉化覆盖情况如下，明细见 [docs/COVERAGE.md](docs/COVERAGE.md)：

| 通道 | 已汉化 | 总量 | 比例 |
| --- | --- | --- | --- |
| 运行时消息目录 `bin\cvimsgs.txt` | 8184 条 | 8586 条 | 95.3% |
| 二进制内嵌字符串（8 个文件） | 169 处 | 169 处 | 100% |
| 欢迎页 `welcome.ini` + `welcome_page.dll` | 23 条 | 23 条 | 100% |
| 帮助文档 `*.chm` | 不在交付范围 | — | — |

未翻译条目均为函数名、窗口类名、`.uir` 类型标识、配置字面值、代码示例及厂商名称。
逐条判定理由见 [docs/UNTRANSLATED.md](docs/UNTRANSLATED.md)。

## 2. 环境要求

| 项目 | 要求 |
| --- | --- |
| 目标软件 | LabWindows/CVI 2015（15.0.0.408），32 位 |
| 操作系统（安装程序） | Windows 7 SP1 / 8.1 / 10 / 11，**64 位**。Windows 7 需已安装 KB2533623（较新的累积更新通常已包含） |
| 操作系统（批处理） | Windows 7 SP1 及以上，32 位或 64 位 |
| Python（批处理方式与源码构建） | 3.8 及以上；Windows 7 推荐 3.8.10 |
| 系统区域设置 | 「非 Unicode 程序的语言」必须为 **中文(简体，中国)**，即 ANSI 代码页 936 |
| 权限 | 对 CVI 安装目录具有写权限；安装到 `Program Files` 时需要管理员权限 |
| 磁盘空间 | 约 55 MB（载荷与原始文件备份各约 26 MB，位于 `%LOCALAPPDATA%`） |
| 不适用的版本 | CVI 2017 / 2019 / 2020 未经验证。消息格式或二进制布局不同时程序会报错退出 |

安装程序为 64 位可执行文件，内置 CPython 3.8.10 运行时与 Visual C++ 运行库，
无需另行安装 Python。32 位 Windows 或未安装 KB2533623 的 Windows 7 请使用
第 3.2 节的批处理方式，该方式只依赖本机 Python，不受上述限制。

## 3. 安装

安装前请完全退出 LabWindows/CVI，包括仍在后台运行的 `cvi.exe`。安装程序会检测该进程，
若仍在运行则中止。

### 3.1 使用单文件安装程序（推荐）

1. 从本仓库 Releases 页面下载 `LabWindowsCVI-zh_CN-v1.0-x64.exe`（约 5 MB）。
2. 可选：核对文件完整性。在 PowerShell 中执行
   `Get-FileHash .\LabWindowsCVI-zh_CN-v1.0-x64.exe -Algorithm SHA256`，
   与 Release 页面给出的 SHA256 一致后再运行。
3. 双击运行。程序自动定位 CVI 安装目录，读取本机文件生成补丁，备份原始文件，
   随后写回安装目录，通常在 2 秒内完成。

当安装目录不可写时，程序才会请求管理员权限；安装到普通目录（例如 `D:\CVI2015`）
不会触发 UAC 提示。输出 `成功 11 个，失败 0 个` 即表示完成。

写入过程中任一文件失败时，程序会把已写入的文件恢复为原始版本，不会留下中英混杂的
安装目录，并返回非零退出码。

安装程序不写入注册表，不创建系统服务或开机启动项。

### 3.2 使用批处理脚本

适用于 32 位系统、Windows 7，或希望先审查脚本再执行的场景。
该方式需本机已安装 Python 3.8 及以上，并执行过一次 `pip install -r requirements.txt`。

```bat
:: 1) 生成补丁文件（只读 CVI 安装目录，不写入）
build.bat "C:\Program Files (x86)\National Instruments\CVI2015"

:: 2) 备份原始文件并写入中文文件
install.bat

:: 3) 需要时还原英文
restore.bat
```

省略参数时，脚本按 `CVI_ROOT` 环境变量、注册表、`Program Files` 的顺序探测安装目录。
安装到 `Program Files` 时请以管理员身份运行 `install.bat`。

也可以完全不使用脚本：`build.bat` 生成的 `payload\` 目录包含 11 个文件，
按 `payload\_files.txt` 中列出的相对路径手工覆盖到安装目录即可。覆盖前请自行备份。

### 3.3 退出码

| 退出码 | 含义 |
| --- | --- |
| 0 | 成功；或已请求提权，实际工作在提权后的进程中完成 |
| 1 | 无需操作（已是中文且未选择还原）、用户放弃，或未找到 CVI |
| 2 | LabWindows/CVI 正在运行 |
| 3 | 无法生成载荷、无可用备份，或备份写入失败 |
| 4 | 写入安装目录失败（已尝试回滚） |
| 5 | 权限不足，提权被取消或提权后仍不可写 |
| 9 | 未预期异常 |

## 4. 还原英文

再次运行安装程序。程序检测到当前为中文界面时会询问是否还原，输入 `y` 并回车。
也可以直接执行：

```bat
LabWindowsCVI-zh_CN-v1.0-x64.exe --restore
```

原始文件备份位于 `%LOCALAPPDATA%\LabWindowsCVI-zh_CN\backup\`，请勿删除。
删除后只能通过重新安装 LabWindows/CVI 恢复英文界面。

备份目录附带 `meta.json`，记录首次安装时 `cvi.exe`、`cvi.dll`、`compile.exe`
的体积指纹。若 CVI 被重装或更换版本，指纹不再匹配，安装程序会将旧备份改名为
`backup.<时间戳>` 保留，并重新备份当前文件，避免把旧版本文件写回新版本安装。

## 5. 注意事项

- 补丁修改本机已安装的软件文件。该行为可能受你与 National Instruments 的许可协议约束，
  请自行确认后再使用。
- 系统区域设置必须为中文(GBK/936)。若开启 Windows 的
  「Beta: 使用 Unicode UTF-8 提供全球语言支持」，GBK 字节会被按 UTF-8 解释，
  界面必然出现乱码，使用前请关闭该选项。
- 安装程序会向安装目录写入文件，并改写 `exe`/`dll` 中的字符串字面量，
  可能触发杀毒软件的启发式规则。源码全部公开，可在核对后加入白名单。
- 本项目只改写 `.rdata` / `.data` 段与 `cvimsgs.txt`，不修改代码段与 PE 结构。
  即便如此，仍建议在安装前对安装目录做一次完整备份。
- CVI 升级或重装后，需要重新运行安装程序。

## 6. 故障排查

| 现象 | 原因与处理 |
| --- | --- |
| 提示「未找到 LabWindows/CVI 安装目录」 | 安装在非默认位置。使用 `--cvi "D:\CVI2015"` 指定安装根目录 |
| 报错「源目录已经是汉化版」 | 当前安装目录已含中文。先执行 `--restore` 还原，再重新安装 |
| 显示安装成功，界面仍为英文 | CVI 未完全退出，文件被占用而未写入；或 CVI 版本与 15.0.0.408 不符。结束所有 `cvi.exe` 后重新安装 |
| 界面出现乱码 | 系统区域设置不是中文(GBK/936)，或开启了 UTF-8 Beta 选项 |
| Windows 7 上双击无反应 | 系统为 32 位，或未安装 KB2533623。改用第 3.2 节的批处理方式 |
| 还原时提示「备份来自另一份 CVI 安装」 | 备份与当前安装的版本指纹不一致。重新安装 CVI，或在确认版本一致后手工恢复 |
| 提示「该目录需要管理员权限」 | 安装目录位于 `Program Files`。在 UAC 提示中选择「是」，或将 CVI 安装到可写目录 |
| 杀毒软件报警或拦截 | 属于对可执行文件的字符串改写行为。核对源码后将安装程序加入白名单 |
| 安装后 CVI 无法启动 | 立即运行 `--restore` 还原。若仍无法启动，使用 CVI 安装介质修复安装 |

## 7. 从源码构建

### 7.1 环境

- Windows 10 / 11（构建机）。目标机器可以是 Windows 7 SP1。
- CPython **3.8.10 x64**。选择 3.8 的原因是 CPython 3.9 起不再支持 Windows 7，
  用更高版本打包出的可执行文件无法在 Windows 7 上启动。
- Nuitka 4.3.5、zstandard 0.23.0、pefile 2024.8.26，版本已固定在
  `requirements-build.txt`。Nuitka 首次构建会自动下载配套的 MinGW-w64 工具链，
  需要网络连接。

```bat
py -3.8 -m pip install -r requirements-build.txt
```

### 7.2 生成补丁载荷

载荷由本机 CVI 安装副本生成，输出到 `payload\`：

```bat
build.bat "C:\Program Files (x86)\National Instruments\CVI2015"
```

等价命令为 `python tools\make_payload.py --cvi "<安装目录>"`。
生成过程只读取 CVI 安装目录，不写入；若源目录已含中文，程序会中止并提示先还原。

### 7.3 打包安装程序

```bat
py -3.8 tools\build_exe.py
```

产物为 `dist\LabWindowsCVI-zh_CN-v1.0-x64.exe`。脚本会检查解释器版本、图标与译文表，
并使用 `--onefile`、`--mingw64`、`--disable-ccache` 等固定参数，
把 `tm\` 译文表一并打包（安装时需要在目标机器上重新生成载荷）。

### 7.4 校验

```bat
python tools\lint_tm.py                  :: 译文表格式、重复 ID、编码、引号
python tools\tmcheck.py                  :: 与英文原文比对格式符与换行数
python tools\patch.py verify --dir payload
python tools\msgpatch.py verify --src "C:\Program Files (x86)\National Instruments\CVI2015\bin" --dir payload\bin
python tools\stats.py                    :: 覆盖率与体积统计
```

`lint_tm.py` 不依赖 CVI，可在任意机器上运行；`tmcheck.py`、`patch.py`、`msgpatch.py`
需要本机存在英文原版 `cvimsgs.txt`（安装程序生成的备份即可满足）。

## 8. 仓库结构

```
LabWindowsCVI-zh_CN/
├─ tools/
│  ├─ setup.py              安装程序入口（打包为单文件 exe）
│  ├─ build_exe.py          Nuitka 打包脚本
│  ├─ make_payload.py       从本机安装生成补丁载荷
│  ├─ patch.py              改写 exe/dll 中的字符串字面量
│  ├─ msgpatch.py           改写消息目录 bin\cvimsgs.txt
│  ├─ msgfile.py            cvimsgs.txt 读写
│  ├─ cviroot.py            定位 CVI 安装目录
│  ├─ paths.py              定位项目根目录（源码与单文件 exe 两种运行方式）
│  ├─ lint_tm.py            译文表静态检查（不需要 CVI）
│  ├─ tmcheck.py            与英文原文比对格式符与换行
│  ├─ stats.py              统计数据
│  ├─ report_untranslated.py 生成未译清单
│  └─ nlfix.py              对齐译文中的换行数量
├─ tm/*.tsv                 译文表，唯一人工维护的数据
├─ assets/icon.ico          安装程序图标
├─ docs/                    术语表、覆盖率、原理、未译清单
├─ build.bat                生成载荷
├─ install.bat              备份并写入
├─ restore.bat              还原英文
├─ requirements.txt         生成载荷所需依赖
└─ requirements-build.txt   打包安装程序所需依赖
```

## 9. 相关文档

| 文档 | 内容 |
| --- | --- |
| [docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md) | 文本通道、原地覆盖的约束、易错点 |
| [docs/GLOSSARY.md](docs/GLOSSARY.md) | 术语表与译名约定 |
| [docs/COVERAGE.md](docs/COVERAGE.md) | 覆盖率与分区明细 |
| [docs/UNTRANSLATED.md](docs/UNTRANSLATED.md) | 保留英文的条目及判定理由 |
| [CHANGELOG.md](CHANGELOG.md) | 变更记录 |
| [NOTICE](NOTICE) | 分层授权与第三方权利说明 |

## 10. 许可与声明

- 代码（`tools/` 与根目录 `*.bat`）采用 MIT 许可，见 [LICENSE](LICENSE)。
- 翻译文本（`tm/`）采用 CC BY-NC-SA 4.0，见 [LICENSE-TRANSLATIONS](LICENSE-TRANSLATIONS)。
- 分层授权的完整说明见 [NOTICE](NOTICE)。

本项目不包含 National Instruments 的任何二进制文件、文档原件或整册译本。
安装所需的补丁载荷由使用者用自己合法持有的安装副本在本机生成，不随本仓库分发。

LabWindows、LabWindows/CVI、CVI、National Instruments 是其各自权利人的商标。
本项目为非官方项目，与 National Instruments 无关联，未获其授权、赞助或背书。

本项目按「现状」提供，不提供任何明示或默示担保。修改本机软件文件存在风险，
使用者应自行评估并承担相应后果。
