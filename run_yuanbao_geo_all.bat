@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion

title Yuanbao GEO One Click Pipeline

cd /d "%~dp0"


rem ============================================================
rem Config
rem ============================================================

set "OUTPUT_ROOT=output"

set "PRODUCT_ID="
set "PRODUCT_NAME="
set "INPUT_CSV="
set "CHECKPOINT_ROOT="

set "YUANBAO_PYTHON=%~dp0.venv\Scripts\python.exe"

set "CDP_URL=http://127.0.0.1:9222/json/version"
set "YUANBAO_URL=https://yuanbao.tencent.com/"

set "CHROME_SESSION_ROOT=%~dp0.chrome-sessions"

for /f %%I in (
    'powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"'
) do (
    set "SESSION_RUN_ID=%%I"
)

set "SESSION_INDEX=0"
set "CHROME_PROFILE="
set "CHROME_EXE="

set "PACKAGE_PATH=%OUTPUT_ROOT%\yuanbao_geo_package.zip"
set "PACKAGE_ABS=%~dp0%PACKAGE_PATH%"


if not exist "%OUTPUT_ROOT%" (
    mkdir "%OUTPUT_ROOT%"
)


rem ============================================================
rem Product menu
rem ============================================================

:PRODUCT_MENU

echo.
echo ============================================================
echo Tencent Yuanbao GEO Collector
echo ============================================================
echo Select product:
echo.
echo [1] 鸿茅药酒
echo [2] 天益寿气血固本口服液
echo [0] Exit
echo ============================================================
echo.

set "PRODUCT_SELECT="
set /p "PRODUCT_SELECT=Select product: "

if "%PRODUCT_SELECT%"=="1" goto :SET_HONGMAO
if "%PRODUCT_SELECT%"=="2" goto :SET_TIANYISHOU
if "%PRODUCT_SELECT%"=="0" exit /b 0

echo.
echo [ERROR] Invalid product selection.
goto :PRODUCT_MENU


:SET_HONGMAO

set "PRODUCT_ID=hongmao_yaojiu"
set "PRODUCT_NAME=鸿茅药酒"
set "INPUT_CSV=input\questions.csv"
set "CHECKPOINT_ROOT=%OUTPUT_ROOT%\checkpoints\hongmao_yaojiu"

goto :MENU


:SET_TIANYISHOU

set "PRODUCT_ID=tianyishou"
set "PRODUCT_NAME=天益寿气血固本口服液"
set "INPUT_CSV=input\tianyishou_questions.csv"
set "CHECKPOINT_ROOT=%OUTPUT_ROOT%\checkpoints\tianyishou"

goto :MENU


rem ============================================================
rem Main menu
rem ============================================================

:MENU

echo.
echo ============================================================
echo Tencent Yuanbao GEO Collector
echo ============================================================
echo [PRODUCT] %PRODUCT_NAME%
echo [PRODUCT ID] %PRODUCT_ID%
echo.
echo [1] Start new collection
echo [2] Resume last unfinished collection
echo [0] Exit
echo ============================================================
echo.

set "RUN_MODE="
set /p "RUN_MODE=Select: "

if "%RUN_MODE%"=="1" goto :NEW_RUN
if "%RUN_MODE%"=="2" goto :RESUME_RUN
if "%RUN_MODE%"=="0" exit /b 0

echo.
echo [ERROR] Invalid selection.
goto :MENU


rem ============================================================
rem New collection
rem ============================================================

:NEW_RUN

set "BATCH_ARG=--new-batch"

goto :RUN_PIPELINE


rem ============================================================
rem Resume
rem ============================================================

:RESUME_RUN

if not exist "%CHECKPOINT_ROOT%\active_batch.json" (
    echo.
    echo [ERROR] No unfinished Yuanbao batch was found.
    echo.
    pause
    goto :MENU
)

set "BATCH_ARG="

echo.
echo [RESUME] Existing unfinished batch will be resumed.
echo.

goto :RUN_PIPELINE


rem ============================================================
rem Pre-check
rem ============================================================

:RUN_PIPELINE

echo.
echo ============================================================
echo Yuanbao GEO One Click Pipeline
echo ============================================================
echo [PRODUCT]    %PRODUCT_NAME%
echo [PRODUCT ID] %PRODUCT_ID%
echo [INPUT]      %INPUT_CSV%
echo [CHECKPOINT] %CHECKPOINT_ROOT%
echo [ZIP]        %PACKAGE_PATH%
echo ============================================================
echo.

if not exist "%YUANBAO_PYTHON%" (
    echo [ERROR] Yuanbao virtualenv Python not found:
    echo %YUANBAO_PYTHON%
    echo.
    echo Run setup_server.bat first.
    goto :FAIL
)

if not exist "%INPUT_CSV%" (
    echo [ERROR] Input CSV not found:
    echo %INPUT_CSV%
    goto :FAIL
)


rem ============================================================
rem 1/3 Chrome Session
rem ============================================================

echo [1/3] Prepare dedicated Chrome session

call :FIND_CHROME

if errorlevel 1 (
    goto :FAIL
)

call :START_NEW_CHROME_SESSION

if errorlevel 1 (
    goto :FAIL
)


rem ============================================================
rem 2/3 Collection
rem ============================================================

:COLLECT_SESSION

echo.
echo [2/3] Run Yuanbao collection
echo [SESSION] !SESSION_INDEX!
echo [PROFILE] !CHROME_PROFILE!
echo.

"%YUANBAO_PYTHON%" ^
    -m scripts.smoke_yuanbao_batch ^
    --product-id "!PRODUCT_ID!" ^
    --input-csv "!INPUT_CSV!" ^
    --checkpoint-root "!CHECKPOINT_ROOT!" ^
    !BATCH_ARG!

set "COLLECT_EXIT=!ERRORLEVEL!"

rem --new-batch is only valid for the first process.
rem Every later Chrome session must resume the same batch.
set "BATCH_ARG="

if "!COLLECT_EXIT!"=="4" (
    goto :ROTATE_SESSION
)

if "!COLLECT_EXIT!"=="2" (
    goto :PAUSED
)

if not "!COLLECT_EXIT!"=="0" (
    echo.
    echo [ERROR] Yuanbao collection incomplete.
    echo [EXIT CODE] !COLLECT_EXIT!
    echo [INFO] Checkpoint remains available.
    goto :FAIL
)

echo.
echo [PASS] Yuanbao collection completed
echo.

call :STOP_CURRENT_CHROME

if errorlevel 1 (
    goto :FAIL
)

goto :BUILD_PACKAGE


rem ============================================================
rem Normal Chrome Session rotation
rem ============================================================

:ROTATE_SESSION

echo.
echo ============================================================
echo SESSION ROTATION
echo ============================================================
echo.
echo Five full questions were completed.
echo Ten answer tasks were saved.
echo.
echo The current Checkpoint is preserved.
echo A fresh Chrome profile will now be opened.
echo.

call :STOP_CURRENT_CHROME

if errorlevel 1 (
    goto :FAIL
)

call :START_NEW_CHROME_SESSION

if errorlevel 1 (
    goto :FAIL
)

goto :COLLECT_SESSION


rem ============================================================
rem 3/3 Package
rem ============================================================

:BUILD_PACKAGE

echo [3/3] Build and verify GEO package

"%YUANBAO_PYTHON%" ^
    -m scripts.smoke_yuanbao_package

if errorlevel 1 (
    echo.
    echo [ERROR] GEO package build failed.
    goto :FAIL
)

if not exist "%PACKAGE_PATH%" (
    echo.
    echo [ERROR] ZIP was not created:
    echo %PACKAGE_PATH%
    goto :FAIL
)

echo.
echo ============================================================
echo SUCCESS
echo ============================================================
echo Yuanbao collection : PASS
echo GEO package        : PASS
echo.
echo ZIP:
echo %PACKAGE_ABS%
echo ============================================================
echo.

explorer.exe /select,"%PACKAGE_ABS%"

pause
exit /b 0


rem ============================================================
rem Chrome helpers
rem ============================================================

:FIND_CHROME

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
    exit /b 1
)

exit /b 0


:START_NEW_CHROME_SESSION

rem Port 9222 must be free before a new managed session starts.
curl.exe -fsS "%CDP_URL%" >nul 2>&1

if not errorlevel 1 (
    echo.
    echo [ERROR] Chrome CDP port 9222 is already in use.
    echo [INFO] Close the old collector Chrome and retry.
    echo.
    exit /b 1
)

set /a SESSION_INDEX+=1

set "SESSION_PAD=00!SESSION_INDEX!"
set "SESSION_PAD=!SESSION_PAD:~-3!"

set "CHROME_PROFILE=!CHROME_SESSION_ROOT!\!SESSION_RUN_ID!_session_!SESSION_PAD!"

if not exist "!CHROME_PROFILE!" (
    mkdir "!CHROME_PROFILE!"
)

echo.
echo ============================================================
echo CHROME SESSION !SESSION_PAD!
echo ============================================================
echo [PROFILE]
echo !CHROME_PROFILE!
echo.

start "" "!CHROME_EXE!" ^
    --remote-debugging-port=9222 ^
    --user-data-dir="!CHROME_PROFILE!" ^
    --no-first-run ^
    --no-default-browser-check ^
    "%YUANBAO_URL%"

powershell -NoProfile -Command ^
"$ok=$false; for($i=0;$i -lt 30;$i++){ try { [void](Invoke-RestMethod -Uri '%CDP_URL%' -TimeoutSec 2); $ok=$true; break } catch { Start-Sleep -Seconds 1 } }; if($ok){exit 0}else{exit 1}"

if errorlevel 1 (
    echo.
    echo [ERROR] Chrome CDP did not become ready.
    exit /b 1
)

echo [PASS] Chrome CDP ready
echo.
echo Please complete the browser step manually:
echo.
echo   1. Sign in to Tencent Yuanbao.
echo   2. Confirm the chat page works normally.
echo   3. Return to this terminal.
echo.
echo No account credentials are entered by this script.
echo.

pause

exit /b 0


:STOP_CURRENT_CHROME

if not defined CHROME_PROFILE (
    exit /b 0
)

echo.
echo [SESSION] Closing current collector Chrome...

set "YUANBAO_ACTIVE_PROFILE=!CHROME_PROFILE!"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$profile=$env:YUANBAO_ACTIVE_PROFILE; Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Where-Object { $_.CommandLine -and $_.CommandLine -like ('*' + $profile + '*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

powershell -NoProfile -Command ^
"$down=$false; for($i=0;$i -lt 20;$i++){ try { [void](Invoke-RestMethod -Uri '%CDP_URL%' -TimeoutSec 1); Start-Sleep -Milliseconds 500 } catch { $down=$true; break } }; if($down){exit 0}else{exit 1}"

if errorlevel 1 (
    echo.
    echo [ERROR] Old Chrome CDP is still active.
    echo [INFO] Close the collector Chrome manually.
    exit /b 1
)

echo [PASS] Current collector Chrome closed

set "CHROME_PROFILE="

exit /b 0


rem ============================================================
rem User intentionally quit during quota switch
rem ============================================================

:PAUSED

call :STOP_CURRENT_CHROME >nul 2>&1

echo.
echo ============================================================
echo COLLECTION PAUSED
echo ============================================================
echo.
echo Current Yuanbao batch is still unfinished.
echo Checkpoint has been preserved.
echo.
echo Run this BAT again.
echo.
echo Select the SAME product first, then select:
echo.
echo   [2] Resume last unfinished collection
echo.
echo Previously successful tasks will be skipped.
echo ============================================================
echo.

pause
exit /b 2


rem ============================================================
rem Failure
rem ============================================================

:FAIL

call :STOP_CURRENT_CHROME >nul 2>&1

echo.
echo ============================================================
echo FAILED OR INCOMPLETE
echo ============================================================
echo.
echo Please read the error above.
echo.
echo If collection was interrupted or failed:
echo run this BAT again and select Resume.
echo.
echo The Checkpoint is NOT deleted automatically.
echo ============================================================
echo.

pause
exit /b 1