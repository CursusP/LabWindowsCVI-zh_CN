@echo off
chcp 936 >nul
setlocal enabledelayedexpansion
pushd "%~dp0"
set "PACK=%CD%"
set "LIST=%PACK%\payload\_files.txt"

echo ==========================================================
echo   LabWindows/CVI 2015  简体中文语言包  -  还原英文
echo ==========================================================
echo.

set "CVI="
if not "%~1"=="" set "CVI=%~1"
if not defined CVI if defined CVI_ROOT set "CVI=%CVI_ROOT%"
if not defined CVI (
  for %%R in (
    "HKLM\SOFTWARE\WOW6432Node\National Instruments\CVI\15.0"
    "HKLM\SOFTWARE\National Instruments\CVI\15.0"
    "HKLM\SOFTWARE\WOW6432Node\National Instruments\CVI"
    "HKLM\SOFTWARE\National Instruments\CVI"
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
if not defined CVI if exist "%ProgramFiles(x86)%\National Instruments\CVI2015\cvi.exe" set "CVI=%ProgramFiles(x86)%\National Instruments\CVI2015"
if not defined CVI if exist "%ProgramFiles%\National Instruments\CVI2015\cvi.exe" set "CVI=%ProgramFiles%\National Instruments\CVI2015"
if defined CVI set "CVI=%CVI:/=\%"
if defined CVI if "%CVI:~-1%"=="\" set "CVI=%CVI:~0,-1%"

if not exist "%CVI%\cvi.exe" (
  echo [错误] 未找到 CVI 安装目录。用法：restore.bat "C:\CVI2015 路径"
  pause
  exit /b 1
)
echo 目标目录: %CVI%

whoami /groups 2>nul | findstr /c:"S-1-16-12288" >nul
if errorlevel 1 (
  echo [提示] 当前不是管理员。若 CVI 安装在 Program Files，下面的写入会全部失败；
  echo        真出现失败，请右键本文件选择「以管理员身份运行」后重试。
  echo.
)

if not exist "%LIST%" (
  echo.
  echo [提示] 未找到 payload，正在用本机安装生成 ...
  call "%PACK%\build.bat" "%CVI%"
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

if not exist "%PACK%\backup" (
  echo [错误] 找不到 backup 目录，无法还原。
  pause
  exit /b 1
)

echo.
set /a OK=0
set /a SKIP=0
for /f "usebackq delims=" %%F in ("%LIST%") do (
  set "REL=%%~F"
  set "REL=!REL:/=\!"
  set "SRC=%PACK%\backup\!REL!"
  set "DST=%CVI%\!REL!"
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
