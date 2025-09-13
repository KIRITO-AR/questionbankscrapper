@echo off
setlocal enabledelayedexpansion

REM Khan Academy Question Bank Scraper - Enhanced Windows Version
REM This script automates the Khan Academy JSON capture using the enhanced scraper

REM --- Configuration ---
set PROXY_PORT=8080
set PROXY_HOST=127.0.0.1
set PYTHON_EXE=D:\collage\questionbankscrapper\.venv\Scripts\python.exe
set ADDON_SCRIPT=capture_khan_json_automated.py
set MITMDUMP_EXE=D:\collage\questionbankscrapper\.venv\Scripts\mitmdump.exe

REM --- Functions ---
:cleanup
echo.
echo [INFO] Cleaning up processes...
taskkill /f /im chrome.exe >nul 2>&1
taskkill /f /im mitmdump.exe >nul 2>&1
echo [INFO] Cleanup complete.
goto :eof

:check_dependencies
REM Check if mitmdump exists
if not exist "%MITMDUMP_EXE%" (
    echo [ERROR] mitmdump not found at: %MITMDUMP_EXE%
    echo         Please ensure mitmproxy is installed in the virtual environment
    exit /b 1
)

REM Check if Python script exists
if not exist "%ADDON_SCRIPT%" (
    echo [ERROR] %ADDON_SCRIPT% not found in current directory
    exit /b 1
)

REM Check if Python executable exists
if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python executable not found at: %PYTHON_EXE%
    exit /b 1
)

echo [INFO] All dependencies found
goto :eof

REM --- Trap cleanup on exit ---
if "%1"=="cleanup" goto cleanup

REM --- Pre-flight checks ---
call :check_dependencies
if errorlevel 1 exit /b 1

REM --- Instructions ---
echo ------------------------------------------------------------------
echo Khan Academy Question Bank Scraper - Enhanced Windows Version
echo ------------------------------------------------------------------
echo [INFO] This tool captures Perseus JSON data from Khan Academy exercises.
echo        Follow these steps:
echo.
echo 1. Chrome will open to Khan Academy with proxy settings
echo 2. Navigate to any math exercise (e.g., practice problems)
echo 3. Start answering questions - they'll be captured automatically
echo 4. Press Ctrl+C here when done capturing
echo.
echo Captured questions will be saved in: khan_academy_json\
echo ------------------------------------------------------------------
echo.

REM Get exercise URL from user if not provided
if "%1"=="" (
    echo [INPUT] Please enter the Khan Academy exercise URL:
    echo         Example: https://www.khanacademy.org/math/algebra/.../e/linear_equations_1
    set /p EXERCISE_URL="Exercise URL: "
) else (
    set EXERCISE_URL=%1
)

REM Validate URL
if "%EXERCISE_URL%"=="" (
    echo [ERROR] No URL provided
    exit /b 1
)

echo "%EXERCISE_URL%" | findstr /c:"khanacademy.org" >nul
if errorlevel 1 (
    echo [ERROR] Please provide a valid Khan Academy URL
    exit /b 1
)

REM Create output directory
if not exist "khan_academy_json" mkdir khan_academy_json

echo [INFO] Starting enhanced Khan Academy scraper...
echo [INFO] Target URL: %EXERCISE_URL%
echo [INFO] Proxy will run on: %PROXY_HOST%:%PROXY_PORT%
echo.

REM --- Main Execution ---
echo [INFO] Starting mitmproxy addon in background...
start /b "" "%MITMDUMP_EXE%" -q -s "%ADDON_SCRIPT%" --listen-port %PROXY_PORT%

REM Wait a moment for mitmproxy to start
timeout /t 3 /nobreak >nul

echo [INFO] Launching Chrome with proxy settings...
start "" "chrome.exe" ^
    --proxy-server=http://%PROXY_HOST%:%PROXY_PORT% ^
    --ignore-certificate-errors ^
    --ignore-ssl-errors ^
    --ignore-certificate-errors-spki-list ^
    --allow-running-insecure-content ^
    --disable-web-security ^
    --new-window ^
    "%EXERCISE_URL%"

echo.
echo [INFO] Chrome launched. Please:
echo        1. Navigate to Khan Academy exercises
echo        2. Start answering questions
echo        3. Questions will be captured automatically
echo.
echo [INFO] Monitoring for captured questions...
echo        Press Ctrl+C to stop capturing
echo.

REM Monitor the output directory for new files
set INITIAL_COUNT=0
if exist "khan_academy_json\*.json" (
    for /f %%i in ('dir /b khan_academy_json\*.json 2^>nul ^| find /c /v ""') do set INITIAL_COUNT=%%i
)

echo [INFO] Initial question count: %INITIAL_COUNT%
echo.

:monitor_loop
timeout /t 10 /nobreak >nul
set CURRENT_COUNT=0
if exist "khan_academy_json\*.json" (
    for /f %%i in ('dir /b khan_academy_json\*.json 2^>nul ^| find /c /v ""') do set CURRENT_COUNT=%%i
)

if !CURRENT_COUNT! gtr %INITIAL_COUNT% (
    set /a NEW_QUESTIONS=!CURRENT_COUNT!-!INITIAL_COUNT!
    echo [SUCCESS] !NEW_QUESTIONS! new questions captured! Total: !CURRENT_COUNT!
    set INITIAL_COUNT=!CURRENT_COUNT!
)

goto monitor_loop

REM This section won't be reached due to the infinite loop above
REM Cleanup happens when user presses Ctrl+C