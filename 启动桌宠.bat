@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动张起灵桌面 Agent...

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" pet_agent.py
) else (
    python pet_agent.py
)

if errorlevel 1 (
    echo.
    echo 程序运行出错，请检查依赖：
    echo python -m pip install PyQt5 pywin32 Pillow requests
    pause
)
