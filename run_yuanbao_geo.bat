@echo off
chcp 65001 >nul
setlocal EnableExtensions

title 腾讯元宝 GEO 一键采集

REM ============================================================
REM 腾讯元宝 GEO 一键执行
REM
REM 流程：
REM 1. 检查 / 启动 Chrome CDP
REM 2. 执行元宝批量采集（自动断点续跑）
REM 3. 生成 GEO 标准 ZIP
REM 4. 中央 GEO 系统校验
REM 5. 中央 GEO 系统正式导入
REM ============================================================


REM =========================
REM 基础路径
REM =========================

set "COLLECTOR_DIR=%~dp0"
set "COLLECTOR_PYTHON=%COLLECTOR_DIR%.venv\Scripts\python.exe"

set "ANALYSIS_DIR=D:\geo_analysis_system"
set "ANALYSIS_PYTHON=%ANALYSIS_DIR%\.venv\Scripts\python.exe"

set "CHROME_EXE=C:\Program Files\Google\Chrome\Application\chrome.exe"

set "CDP_URL=http://127.0.0.1:9222/json/version"

set "PACKAGE_PATH=%COLLECTOR_DIR%output\yuanbao_geo_package.zip"


echo.
echo ============================================================
echo 腾讯元宝 GEO 一键采集系统
echo ============================================================
echo.


REM =========================
REM 1. 环境检查
REM =========================

echo [1/7] 检查运行环境...

if not exist "%COLLECTOR_PYTHON%" (
    echo.
    echo [ERROR] 未找到元宝采集器 Python：
    echo %COLLECTOR_PYTHON%
    goto :FAILED
)

if not exist "%ANALYSIS_PYTHON%" (
    echo.
    echo [ERROR] 未找到中央分析系统 Python：
    echo %ANALYSIS_PYTHON%
    goto :FAILED
)

if not exist "%CHROME_EXE%" (
    echo.
    echo [ERROR] 未找到 Chrome：
    echo %CHROME_EXE%
    goto :FAILED
)

echo [OK] 运行环境正常
echo.


REM =========================
REM 2. 检查 Chrome CDP
REM =========================

echo [2/7] 检查 Chrome CDP 9222...

powershell -NoProfile -Command ^
    "try { Invoke-WebRequest -UseBasicParsing '%CDP_URL%' -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"

if not errorlevel 1 (
    echo [OK] Chrome CDP 已运行
    goto :CDP_READY
)

echo [INFO] Chrome CDP 未运行，正在自动启动...

start "" "%CHROME_EXE%" ^
    --remote-debugging-port=9222 ^
    --user-data-dir="%COLLECTOR_DIR%.chrome-profile"


REM =========================
REM 3. 等待 CDP
REM =========================

echo [3/7] 等待 Chrome CDP 就绪...

set /a WAIT_COUNT=0

:WAIT_CDP

set /a WAIT_COUNT+=1

powershell -NoProfile -Command ^
    "try { Invoke-WebRequest -UseBasicParsing '%CDP_URL%' -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }"

if not errorlevel 1 (
    goto :CDP_READY
)

if %WAIT_COUNT% GEQ 30 (
    echo.
    echo [ERROR] 等待 Chrome CDP 超时
    goto :FAILED
)

timeout /t 1 /nobreak >nul

goto :WAIT_CDP


:CDP_READY

echo [OK] Chrome CDP 已就绪
echo.


REM =========================
REM 4. 元宝批量采集
REM =========================

echo ============================================================
echo [4/7] 开始腾讯元宝 GEO 批量采集
echo ============================================================
echo.

cd /d "%COLLECTOR_DIR%"

"%COLLECTOR_PYTHON%" -m scripts.smoke_yuanbao_batch

if errorlevel 1 (
    echo.
    echo [ERROR] 元宝批量采集执行失败
    echo [INFO] Checkpoint 已保留，下次重新双击可继续运行
    goto :FAILED
)

echo.
echo [OK] 元宝批量采集完成
echo.


REM =========================
REM 5. GEO 标准包
REM =========================

echo ============================================================
echo [5/7] 生成 GEO 标准 ZIP
echo ============================================================
echo.

"%COLLECTOR_PYTHON%" -m scripts.smoke_yuanbao_package

if errorlevel 1 (
    echo.
    echo [ERROR] GEO 标准包生成失败
    goto :FAILED
)

if not exist "%PACKAGE_PATH%" (
    echo.
    echo [ERROR] 未找到生成的 GEO ZIP：
    echo %PACKAGE_PATH%
    goto :FAILED
)

echo.
echo [OK] GEO 标准包生成成功
echo %PACKAGE_PATH%
echo.


REM =========================
REM 6. 中央系统校验
REM =========================

echo ============================================================
echo [6/7] 中央 GEO 系统校验标准包
echo ============================================================
echo.

cd /d "%ANALYSIS_DIR%"

"%ANALYSIS_PYTHON%" .\scripts\import_platform_package.py ^
    --package "%PACKAGE_PATH%" ^
    --validate-only

if errorlevel 1 (
    echo.
    echo [ERROR] 中央 GEO 系统校验失败
    echo [INFO] 为保护数据库，本次不会执行正式导入
    goto :FAILED
)

echo.
echo [OK] 中央 GEO 标准包校验通过
echo.


REM =========================
REM 7. 正式导入中央系统
REM =========================

echo ============================================================
echo [7/7] 正式导入中央 GEO 系统
echo ============================================================
echo.

"%ANALYSIS_PYTHON%" .\scripts\import_platform_package.py ^
    --package "%PACKAGE_PATH%"

if errorlevel 1 (
    echo.
    echo [ERROR] 中央 GEO 系统正式导入失败
    goto :FAILED
)


REM =========================
REM 全部成功
REM =========================

echo.
echo ============================================================
echo                 GEO 全流程执行成功
echo ============================================================
echo.
echo 腾讯元宝采集      ：PASS
echo GEO 标准包        ：PASS
echo 中央系统校验      ：PASS
echo 中央系统导入      ：PASS
echo.
echo 标准包：
echo %PACKAGE_PATH%
echo.
echo ============================================================

pause

exit /b 0


:FAILED

echo.
echo ============================================================
echo                 GEO 全流程执行失败
echo ============================================================
echo.
echo 请查看上方 ERROR 信息。
echo.
echo 如果采集阶段中断：
echo 再次双击本文件即可利用 Checkpoint 继续未完成批次。
echo.
echo ============================================================

pause

exit /b 1