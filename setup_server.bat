@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

title Yuanbao GEO Server Setup

cd /d "%~dp0"

set "YUANBAO_PYTHON=%~dp0.venv\Scripts\python.exe"


echo ============================================================
echo Yuanbao GEO Server Setup
echo ============================================================
echo Project:
echo %CD%
echo.


rem ============================================================
rem 1/5 Python
rem ============================================================

echo [1/5] Check Python 3.11

python --version >nul 2>&1

if errorlevel 1 (
    echo [ERROR] Python was not found.
    echo Please install Python 3.11 x64 first.
    goto :FAIL
)

for /f "tokens=2" %%V in (
    'python --version 2^>^&1'
) do (
    set "PYTHON_VERSION=%%V"
)

echo [INFO] Python !PYTHON_VERSION!

for /f "tokens=1,2 delims=." %%A in (
    "!PYTHON_VERSION!"
) do (
    set "PY_MAJOR=%%A"
    set "PY_MINOR=%%B"
)

if not "!PY_MAJOR!"=="3" (
    echo [ERROR] Python 3.11 is required.
    goto :FAIL
)

if not "!PY_MINOR!"=="11" (
    echo [ERROR] Python 3.11 is required.
    goto :FAIL
)

echo [PASS] Python 3.11 ready
echo.


rem ============================================================
rem 2/5 Chrome
rem ============================================================

echo [2/5] Check Google Chrome

set "CHROME_EXE="

if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
)

if not defined CHROME_EXE (
    if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
        set "CHROME_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
    )
)

if not defined CHROME_EXE (
    if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
        set "CHROME_EXE=%LocalAppData%\Google\Chrome\Application\chrome.exe"
    )
)

if not defined CHROME_EXE (
    echo [ERROR] Google Chrome was not found.
    echo Install Google Chrome and run setup again.
    goto :FAIL
)

echo [PASS] Chrome found:
echo !CHROME_EXE!
echo.


rem ============================================================
rem 3/5 Virtual environment
rem ============================================================

echo [3/5] Prepare Python virtual environment

if not exist "%YUANBAO_PYTHON%" (

    python -m venv .venv

    if errorlevel 1 (
        echo [ERROR] Failed to create .venv
        goto :FAIL
    )
)

if not exist "%YUANBAO_PYTHON%" (
    echo [ERROR] Virtualenv Python was not created.
    goto :FAIL
)

echo [PASS] Virtualenv ready
echo.


rem ============================================================
rem 4/5 Dependencies
rem ============================================================

echo [4/5] Install Python dependencies

"%YUANBAO_PYTHON%" -m pip install --upgrade pip

if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip.
    goto :FAIL
)

"%YUANBAO_PYTHON%" -m pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install requirements.txt
    goto :FAIL
)

echo [PASS] Python dependencies installed
echo.


rem ============================================================
rem 5/5 Self check
rem ============================================================

echo [5/5] Run project self-check

"%YUANBAO_PYTHON%" -m pip check

if errorlevel 1 (
    echo [ERROR] pip check failed.
    goto :FAIL
)

"%YUANBAO_PYTHON%" -m compileall app scripts

if errorlevel 1 (
    echo [ERROR] compileall failed.
    goto :FAIL
)

"%YUANBAO_PYTHON%" -c "from app.core.config import get_settings; from app.yuanbao.client import YuanbaoClient; from app.yuanbao.runner import YuanbaoBatchRunner; print('Yuanbao imports OK')"

if errorlevel 1 (
    echo [ERROR] Yuanbao import self-check failed.
    goto :FAIL
)

if not exist "output" (
    mkdir output
)

if not exist "output\checkpoints" (
    mkdir output\checkpoints
)


echo.
echo ============================================================
echo SERVER SETUP SUCCESS
echo ============================================================
echo.
echo Next:
echo.
echo 1. Run run_yuanbao_geo_all.bat
echo 2. Chrome will open automatically if CDP is not running.
echo 3. Sign in to Tencent Yuanbao manually.
echo 4. Return to the terminal and continue.
echo.
echo Account switching and human verification remain manual.
echo ============================================================
echo.

pause
exit /b 0


:FAIL

echo.
echo ============================================================
echo SERVER SETUP FAILED
echo ============================================================
echo Please read the error above and run setup again.
echo ============================================================
echo.

pause
exit /b 1