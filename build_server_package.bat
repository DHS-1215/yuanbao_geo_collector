@echo off
chcp 65001 >nul
setlocal EnableExtensions

title Build Yuanbao GEO Server Package

cd /d "%~dp0"

set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Development virtualenv was not found:
    echo %PYTHON_EXE%
    pause
    exit /b 1
)

"%PYTHON_EXE%" scripts\build_server_package.py

if errorlevel 1 (
    echo.
    echo [ERROR] Server package build failed.
    pause
    exit /b 1
)

echo.
echo [PASS] Server package created.
echo.

pause
exit /b 0
