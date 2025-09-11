@echo off
REM Khan Academy Automated Question Scraper for Windows
REM This script runs the fully automated question scraping system

echo.
echo ================================================================
echo Khan Academy Automated Question Scraper
echo ================================================================
echo.

REM Check if virtual environment Python is available
if exist ".venv\Scripts\python.exe" (
    set PYTHON_CMD=.venv\Scripts\python.exe
    echo Using virtual environment Python
) else (
    REM Check if Python is available globally
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python is not installed or not in PATH
        echo Please install Python 3.7+ and try again
        pause
        exit /b 1
    )
    set PYTHON_CMD=python
    echo Using system Python
)

REM Check if required files exist
if not exist "automated_scraper.py" (
    echo [ERROR] automated_scraper.py not found in current directory
    pause
    exit /b 1
)

if not exist "capture_khan_json_automated.py" (
    echo [ERROR] capture_khan_json_automated.py not found in current directory
    pause
    exit /b 1
)

REM Check dependencies
echo Checking dependencies...
%PYTHON_CMD% automated_scraper.py --check-deps

REM Get exercise URL from user if not provided
if "%1"=="" (
    echo.
    echo Please provide a Khan Academy exercise URL
    echo Example: https://www.khanacademy.org/math/algebra/x2f8bb11595b61c86:quadratic-functions-equations/x2f8bb11595b61c86:quadratic-formula/e/quadratic_formula
    echo.
    set /p EXERCISE_URL="Enter exercise URL: "
) else (
    set EXERCISE_URL=%1
)

REM Validate URL
echo %EXERCISE_URL% | findstr "khanacademy.org" >nul
if errorlevel 1 (
    echo [ERROR] Invalid Khan Academy URL
    pause
    exit /b 1
)

echo.
echo Starting automated scraper...
echo Target URL: %EXERCISE_URL%
echo.
echo The scraper will:
echo 1. Start mitmproxy to intercept HTTP traffic
echo 2. Launch browser automation to trigger question loading
echo 3. Automatically download all question JSONs
echo 4. Refresh periodically to get new question sets
echo.
echo Press Ctrl+C to stop the scraper
echo.

REM Run the automated scraper
%PYTHON_CMD% automated_scraper.py "%EXERCISE_URL%"

echo.
echo Scraping session completed.
pause