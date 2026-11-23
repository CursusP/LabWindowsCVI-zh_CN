@echo off
chcp 936 >nul
setlocal enabledelayedexpansion
pushd "%~dp0"
set "PACK=%CD%"
set "LIST=%PACK%\payload\_files.txt"

echo ==========================================================
echo   LabWindows/CVI 2015  简体中文语言包  -  安装
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
  echo [错误] 未找到 LabWindows/CVI 安装目录。
  echo        请显式指定：install.bat "C:\Program Files (x86)\National Instruments\CVI2015"
  echo.
  pause
  exit /b 1
)
echo 目标目录: %CVI%

if exist "%PACK%\backup_source.txt" (
  set /p PREV=<"%PACK%\backup_source.txt"
  if /i not "!PREV!"=="%CVI%" (
    echo [警告] 现有备份来自另一份安装：!PREV!
    echo        继续会把旧版本文件写进当前目录。请先把 backup 目录改名再重试。
    echo.
  )
)


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
  echo.
  echo [错误] LabWindows/CVI 正在运行，请先关闭。
  pause
  exit /b 1
)

echo.
echo [1/3] 备份原始文件到 %PACK%\backup ...
set /a BAKED=0
for /f "usebackq delims=" %%F in ("%LIST%") do (
  set "REL=%%~F"
  set "REL=!REL:/=\!"
  set "DST=%CVI%\!REL!"
  if exist "!DST!" (
    if not exist "%PACK%\backup\!REL!" (
      for %%D in ("%PACK%\backup\!REL!") do (
        if not exist "%%~dpD" mkdir "%%~dpD" >nul 2>&1
      )
      copy /y "!DST!" "%PACK%\backup\!REL!" >nul 2>&1
      set /a BAKED+=1
    )
  )
)
if not exist "%PACK%\backup" mkdir "%PACK%\backup" >nul 2>&1
if not exist "%PACK%\backup_source.txt" >"%PACK%\backup_source.txt" echo %CVI%
echo       已备份 !BAKED! 个文件

echo.
echo [2/3] 写入中文文件 ...
set /a OK=0
set /a FAIL=0
for /f "usebackq delims=" %%F in ("%LIST%") do (
  set "REL=%%~F"
  set "REL=!REL:/=\!"
  set "SRC=%PACK%\payload\!REL!"
  set "DST=%CVI%\!REL!"
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
