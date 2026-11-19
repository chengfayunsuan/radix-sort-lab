@echo off
rem ============================================================
rem  基数排序可视化 · 一键启动
rem
rem  启动优先级：
rem    1) 本机 uv 安装的 Python（无黑框 GUI 版），这是开发机上确认可用的解释器
rem    2) Python 官方启动器 pyw（GUI 版，不弹控制台）
rem    3) 回退到 py（带控制台，出错时能看到信息）
rem  换一台机器如果第 1 条路径不对，会自动走第 2、3 条。
rem ============================================================

cd /d "%~dp0"

set "UV_PYW=C:\Users\57436\AppData\Roaming\uv\python\cpython-3.12.14-windows-x86_64-none\pythonw.exe"
if exist "%UV_PYW%" (
    start "" "%UV_PYW%" "%~dp0main.py"
    exit /b
)

where pyw >nul 2>nul
if not errorlevel 1 (
    start "" pyw "%~dp0main.py"
    exit /b
)

where py >nul 2>nul
if not errorlevel 1 (
    py "%~dp0main.py"
    pause
    exit /b
)

echo 没有找到可用的 Python，请先安装 Python 3。
pause
