@echo off
rem ============================================================
rem  基数排序可视化 · 一键启动
rem  启动优先级：本机 uv Python（无黑框） > pyw > py
rem ============================================================

cd /d "%~dp0"

set "UV_PYW=C:\Users\57436\AppData\Roaming\uv\python\cpython-3.12.14-windows-x86_64-none\pythonw.exe"
if exist "%UV_PYW%" goto useuv

where pyw >nul 2>nul
if %errorlevel%==0 goto usepyw

where py >nul 2>nul
if %errorlevel%==0 goto usepy

echo 没有找到可用的 Python，请先安装 Python 3。
pause
exit /b

:useuv
start "" "%UV_PYW%" "%~dp0main.py"
exit /b

:usepyw
start "" pyw "%~dp0main.py"
exit /b

:usepy
py "%~dp0main.py"
pause
exit /b
