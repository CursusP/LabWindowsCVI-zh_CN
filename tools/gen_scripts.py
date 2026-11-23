#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 install.bat / restore.bat（GBK + CRLF）。

注意：本脚本必须以文件形式保存后执行，不要用 heredoc 传内联源码，
否则反斜杠可能在传递过程中被改写成正斜杠，导致 if exist 判断失败。
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
B = chr(92)          # 反斜杠
Q = '"'

# 三个 .bat 共用的安装目录探测逻辑：参数 → CVI_ROOT → 注册表 → Program Files。
# 顺序与 tools/cviroot.py 保持一致，避免「bat 找得到、python 找不到」。
DETECT = r'''set "CVI="
if not "%~1"=="" set "CVI=%~1"
if not defined CVI if defined CVI_ROOT set "CVI=%CVI_ROOT%"
if not defined CVI (
  for %%R in (
    "HKLM@BS@SOFTWARE@BS@WOW6432Node@BS@National Instruments@BS@CVI@BS@15.0"
    "HKLM@BS@SOFTWARE@BS@National Instruments@BS@CVI@BS@15.0"
    "HKLM@BS@SOFTWARE@BS@WOW6432Node@BS@National Instruments@BS@CVI"
    "HKLM@BS@SOFTWARE@BS@National Instruments@BS@CVI"
  ) do (
    if not defined CVI (
      for %%V in (InstallDir Path InstallLocation) do (
        if not defined CVI (
          for /f "tokens=2,*" %%A in ('reg query %%R /v %%V 2^>nul ^| findstr /i /c:"%%V"') do set "CVI=%%B"
        )
      )
    )
  )
)
if not defined CVI if exist "%ProgramFiles(x86)%@BS@National Instruments@BS@CVI2015@BS@cvi.exe" set "CVI=%ProgramFiles(x86)%@BS@National Instruments@BS@CVI2015"
if not defined CVI if exist "%ProgramFiles%@BS@National Instruments@BS@CVI2015@BS@cvi.exe" set "CVI=%ProgramFiles%@BS@National Instruments@BS@CVI2015"
if defined CVI set "CVI=%CVI:/=@BS@%"
if defined CVI if "%CVI:~-1%"=="@BS@" set "CVI=%CVI:~0,-1%"
'''

# 写安装目录前先看权限：CVI 默认装在 Program Files，普通权限下 copy 会全部失败，
# 用户看到的是「成功 0 个」而不是「权限不足」。用完整性级别判断，不依赖 Server 服务。
ADMINCHK = r'''whoami /groups 2>nul | findstr /c:"S-1-16-12288" >nul
if errorlevel 1 (
  echo [提示] 当前不是管理员。若 CVI 安装在 Program Files，下面的写入会全部失败；
  echo        真出现失败，请右键本文件选择「以管理员身份运行」后重试。
  echo.
)
'''

INSTALL = r'''@echo off
chcp 936 >nul
setlocal enabledelayedexpansion
pushd "%~dp0"
set "PACK=%CD%"
set "LIST=%PACK%@BS@payload@BS@_files.txt"

echo ==========================================================
echo   LabWindows/CVI 2015  简体中文语言包  -  安装
echo ==========================================================
echo.

@DETECT@
if not exist "%CVI%@BS@cvi.exe" (
  echo [错误] 未找到 LabWindows/CVI 安装目录。
  echo        请显式指定：install.bat "C:@BS@Program Files (x86)@BS@National Instruments@BS@CVI2015"
  echo.
  pause
  exit /b 1
)
echo 目标目录: %CVI%

if exist "%PACK%@BS@backup_source.txt" (
  set /p PREV=<"%PACK%@BS@backup_source.txt"
  if /i not "!PREV!"=="%CVI%" (
    echo [警告] 现有备份来自另一份安装：!PREV!
    echo        继续会把旧版本文件写进当前目录。请先把 backup 目录改名再重试。
    echo.
  )
)


@ADMIN@
if not exist "%LIST%" (
  echo.
  echo [提示] 未找到 payload，正在用本机安装生成 ...
  call "%PACK%@BS@build.bat" "%CVI%"
  if not exist "%LIST%" (
    echo [错误] 生成 payload 失败，请查看上方输出。
    pause
    exit /b 1
  )
)

tasklist /fi "imagename eq cvi.exe" 2>nul | findstr /i /c:"cvi.exe" >nul
if not errorlevel 1 (
  echo.
  echo [错误] LabWindows/CVI 正在运行，请先关闭。
  pause
  exit /b 1
)

echo.
echo [1/3] 备份原始文件到 %PACK%@BS@backup ...
set /a BAKED=0
for /f "usebackq delims=" %%F in ("%LIST%") do (
  set "REL=%%~F"
  set "REL=!REL:/=@BS@!"
  set "DST=%CVI%@BS@!REL!"
  if exist "!DST!" (
    if not exist "%PACK%@BS@backup@BS@!REL!" (
      for %%D in ("%PACK%@BS@backup@BS@!REL!") do (
        if not exist "%%~dpD" mkdir "%%~dpD" >nul 2>&1
      )
      copy /y "!DST!" "%PACK%@BS@backup@BS@!REL!" >nul 2>&1
      set /a BAKED+=1
    )
  )
)
if not exist "%PACK%@BS@backup" mkdir "%PACK%@BS@backup" >nul 2>&1
if not exist "%PACK%@BS@backup_source.txt" >"%PACK%@BS@backup_source.txt" echo %CVI%
echo       已备份 !BAKED! 个文件

echo.
echo [2/3] 写入中文文件 ...
set /a OK=0
set /a FAIL=0
for /f "usebackq delims=" %%F in ("%LIST%") do (
  set "REL=%%~F"
  set "REL=!REL:/=@BS@!"
  set "SRC=%PACK%@BS@payload@BS@!REL!"
  set "DST=%CVI%@BS@!REL!"
  for %%D in ("!DST!") do (
    if not exist "%%~dpD" mkdir "%%~dpD" >nul 2>&1
  )
  copy /y "!SRC!" "!DST!" >nul 2>&1
  if errorlevel 1 (
    echo       [失败] !REL!
    set /a FAIL+=1
  ) else (
    echo       [完成] !REL!
    set /a OK+=1
  )
)

echo.
echo [3/3] 结果
echo       成功 !OK! 个，失败 !FAIL! 个
if !FAIL! gtr 0 (
  echo       请关闭 CVI，并确认对目标目录有写入权限
  echo       ^(可能需要以管理员身份运行^)。
) else (
  echo       安装完成，启动 LabWindows/CVI 即为中文界面。
  echo       如需还原英文，运行 restore.bat。
)
echo.
popd
pause
'''

RESTORE = r'''@echo off
chcp 936 >nul
setlocal enabledelayedexpansion
pushd "%~dp0"
set "PACK=%CD%"
set "LIST=%PACK%@BS@payload@BS@_files.txt"

echo ==========================================================
echo   LabWindows/CVI 2015  简体中文语言包  -  还原英文
echo ==========================================================
echo.

@DETECT@
if not exist "%CVI%@BS@cvi.exe" (
  echo [错误] 未找到 CVI 安装目录。用法：restore.bat "C:@BS@CVI2015 路径"
  pause
  exit /b 1
)
echo 目标目录: %CVI%

@ADMIN@
if not exist "%LIST%" (
  echo.
  echo [提示] 未找到 payload，正在用本机安装生成 ...
  call "%PACK%@BS@build.bat" "%CVI%"
  if not exist "%LIST%" (
    echo [错误] 生成 payload 失败，请查看上方输出。
    pause
    exit /b 1
  )
)

tasklist /fi "imagename eq cvi.exe" 2>nul | findstr /i /c:"cvi.exe" >nul
if not errorlevel 1 (
  echo [错误] LabWindows/CVI 正在运行，请先关闭。
  pause
  exit /b 1
)

if not exist "%PACK%@BS@backup" (
  echo [错误] 找不到 backup 目录，无法还原。
  pause
  exit /b 1
)

echo.
set /a OK=0
set /a SKIP=0
for /f "usebackq delims=" %%F in ("%LIST%") do (
  set "REL=%%~F"
  set "REL=!REL:/=@BS@!"
  set "SRC=%PACK%@BS@backup@BS@!REL!"
  set "DST=%CVI%@BS@!REL!"
  if exist "!SRC!" (
    copy /y "!SRC!" "!DST!" >nul 2>&1
    if errorlevel 1 (
      echo       [失败] !REL!
    ) else (
      echo       [还原] !REL!
      set /a OK+=1
    )
  ) else (
    set /a SKIP+=1
  )
)

echo.
echo       已还原 !OK! 个文件，跳过 !SKIP! 个（无备份）
echo.
popd
pause
'''


BUILD = r"""@echo off
chcp 936 >nul
setlocal enabledelayedexpansion
pushd "%~dp0"
set "PACK=%CD%"

echo ==========================================================
echo   LabWindows/CVI 2015  简体中文语言包  -  生成载荷
echo ==========================================================
echo.

@DETECT@
if not exist "%CVI%@BS@cvi.exe" (
  echo [错误] 未找到 LabWindows/CVI 安装目录。
  echo        用法：build.bat "C:@BS@Program Files (x86)@BS@National Instruments@BS@CVI2015"
  popd
  pause
  exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
  echo [错误] 需要 Python 3（用于应用翻译）。请先安装并加入 PATH。
  popd
  pause
  exit /b 1
)
rem Windows 10 自带的 python.exe 可能只是应用商店占位符，执行即失败
python -c "import sys" >nul 2>&1
if errorlevel 1 (
  echo [错误] 找到的 python 无法运行，可能只是应用商店占位符。
  echo        请安装 Python 3.8 或更高版本，并在安装时勾选 Add to PATH。
  popd
  pause
  exit /b 1
)

python "%PACK%@BS@tools@BS@make_payload.py" --cvi "%CVI%"
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
  echo [错误] 生成失败，返回码 %RC%
) else (
  echo 载荷已生成到 payload@BS@
)
popd
pause
"""

def write_bat(name, text):
    text = text.replace("@DETECT@", DETECT)
    text = text.replace("@ADMIN@", ADMINCHK)
    text = text.replace("@BS@", B)
    text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    path = os.path.join(ROOT, name)
    with open(path, "wb") as f:
        f.write(text.encode("gbk"))
    print(f"{name}: {os.path.getsize(path)} bytes")


if __name__ == "__main__":
    write_bat("install.bat", INSTALL)
    write_bat("restore.bat", RESTORE)
    write_bat("build.bat", BUILD)
