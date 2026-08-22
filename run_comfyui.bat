@echo off
setlocal

REM Move to the folder where this BAT file is located.
cd /d "%~dp0"

REM Check virtual environment.
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] .venv was not found.
    echo Create it first with:
    echo   py -3.12 -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Check ComfyUI entry point.
if not exist "main.py" (
    echo [ERROR] main.py was not found.
    echo Put this BAT file in the ComfyUI-JP-Enhanced root folder.
    echo.
    pause
    exit /b 1
)

echo ==========================================
echo   ComfyUI-JP-Enhanced
echo ==========================================
echo.
echo Starting ComfyUI...
echo URL: http://127.0.0.1:8188
echo.

set PYTHONUTF8=1

".venv\Scripts\python.exe" main.py --port 8188

echo.
echo ComfyUI has stopped.
pause
endlocal
