# 术语表

翻译时的唯一来源。新增词条请先查此表，**同一英文词只允许一种译法**。

## 核心术语

| 英文 | 中文 | 说明 / 禁用译法 |
|---|---|---|
| project | 工程 | 不译「项目」 |
| workspace | 工作区 | 不译「工作空间」 |
| build | 生成 | 不译「构建」；`Build Project` = 生成工程 |
| rebuild | 重新生成 | |
| compile | 编译 | 与「生成」区分：compile 只到目标文件 |
| link | 链接 | |
| target | 目标 | 目标文件 / 目标设置 / 执行目标 |
| configuration | 配置 | 生成配置、发布配置 |
| distribution | 发布包 | 不译「分发」 |
| installer | 安装程序 | |
| patch | 补丁 | |
| function panel | 函数面板 | |
| function tree | 函数树 | |
| instrument | 仪器 | instrument driver = 仪器驱动程序 |
| instrument driver | 仪器驱动程序 | 首次出现后可用「驱动程序」 |
| attribute | 属性 | |
| control | 控件 | 绝不译为「控制」 |
| callback | 回调函数 | |
| panel | 面板 | |
| menu bar | 菜单栏 | menu item = 菜单项 |
| toolbar | 工具栏 | |
| shortcut | 快捷方式 | |
| registry key | 注册表项 | registry value = 注册表值 |
| breakpoint | 断点 | |
| watch expression | 监视表达式 | |
| call stack | 调用栈 | |
| thread | 线程 | |
| debug / debugging | 调试 | |
| release (n.) | 发布 | release configuration = 发布配置 |
| run-time engine | 运行时引擎 | |
| side-by-side | 并行 | side-by-side run-time = 并行运行时 |
| merge module | 合并模块 | |
| source code control | 源码控制 | 待确认：如团队用「版本控制」需全局替换 |
| checkout / check in | 签出 / 签入 | |
| interactive execution | 交互式执行 | |
| user interface | 用户界面 | |
| resource file | 资源文件 | |
| include file | 包含文件 | 不译「头文件」以外的说法混用 |

## 明确不翻译

- 函数名、宏名、类型名、API 名：`InitCVIRTE`、`LoadPanel`、`ViStatus`
- 快捷键与修饰键：`Ctrl+O`、`Alt+F4`、`Shift`
- 版本号、路径、文件扩展名：`.uir`、`.fp`、`.cds`、`.msi`
- 厂商与产品名：`National Instruments`、`LabWindows/CVI`、`NI-DAQmx`、`VISA`、`GPIB`、`VXI`、`PXI`
- 总线与协议名：`Ethernet`（可写作「以太网」）、`DeviceNet`、`TCP`、`USB`
- 注册表值类型：`REG_SZ`、`REG_DWORD`、`REG_BINARY`
- 安装位置令牌：`[Program Files]`、`[Temp]`、`[CVI]`（同时是 `.cds` 里的标识符）
- 配置字面值：`True`、`False`、`Standard`、`Extended`

## 标点与格式约定

- 中文句子用全角标点；括号用全角 `（）`，但包裹英文/代码时用半角。
- 保留原文的 `\n` 数量与位置，不自行增删空行。
- 保留格式说明符的顺序：`%s` / `%d` 的**出现顺序**必须与原文一致，否则 `msgpatch.py` 拒绝写入。
- 译文不得含半角双引号 `"`：会破坏 `.cvimsgs` 的字面量结构；需要引号时用 `“”`。
- 中文标签不保留助记符（不加 `__X` / `&X`）。
