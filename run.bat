@echo off
rem ============================================================
rem  基数排序可视化 · 一键启动
rem
rem  用 pyw 启动：走 Python 官方启动器（和 py 是同一个解释器），
rem  但它是 GUI 版本，不会弹出黑色控制台窗口。
rem  如果你的机器上没有 py 启动器，会自动回退到带控制台的 py。
rem ============================================================

cd /d "%~dp0"

where pyw >nul 2>nul
if not %errorlevel%==0 goto console

start "" pyw "%~dp0main.py"
exit /b

:console
py "%~dp0main.py"
pause
