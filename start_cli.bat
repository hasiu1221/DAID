@echo off
cd /d "%~dp0"
echo ========================================================
echo   Uruchamianie Systemu Walki RPG (Rich TUI)...
echo ========================================================
.\.venv\Scripts\python.exe run_cli.py
pause
