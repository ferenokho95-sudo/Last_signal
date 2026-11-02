@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 main.py
) else (
    python main.py
)
if errorlevel 1 (
    echo.
    echo Game failed to start. Install Python 3.10+ with Tcl/Tk.
    pause
)
