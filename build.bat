@echo off
chcp 936 >nul
setlocal enabledelayedexpansion
pushd "%~dp0"
set "PACK=%CD%"

echo ==========================================================
echo   LabWindows/CVI 2015  简体中文语言包  -  生成载荷
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
  echo        用法：build.bat "C:\Program Files (x86)\National Instruments\CVI2015"
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

python "%PACK%\tools\make_payload.py" --cvi "%CVI%"
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
  echo [错误] 生成失败，返回码 %RC%
) else (
  echo 载荷已生成到 payload\
)
popd
pause
