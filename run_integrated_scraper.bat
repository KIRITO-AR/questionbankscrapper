@echo off
echo.
echo ============================================================
echo INTEGRATED KHAN ACADEMY QUESTION SCRAPER
echo ============================================================
echo.

:: Check if URL provided
if "%1"=="" (
    echo Error: Khan Academy exercise URL required
    echo.
    echo Usage: %0 ^<exercise_url^> [timeout_minutes]
    echo.
    echo Example:
    echo   %0 "https://www.khanacademy.org/math/algebra-home/alg-linear-eq-func/graphing-slope-intercept/e/graph-from-slope-intercept-form" 60
    echo.
    echo Tip: Copy the URL from Khan Academy math exercise page
    pause
    exit /b 1
)

:: Set virtual environment
set PYTHON_EXE=D:\collage\questionbankscrapper\.venv\Scripts\python.exe

:: Check if Python exists
if not exist "%PYTHON_EXE%" (
    echo Error: Python virtual environment not found at:
    echo %PYTHON_EXE%
    echo.
    echo Please run: python -m venv .venv
    echo Then activate and install requirements: pip install mitmproxy selenium
    pause
    exit /b 1
)

:: Set timeout (default 30 minutes if not provided)
set TIMEOUT_MINUTES=%2
if "%TIMEOUT_MINUTES%"=="" set TIMEOUT_MINUTES=30

echo Starting integrated Khan Academy scraper...
echo Target URL: %1
echo Timeout: %TIMEOUT_MINUTES% minutes
echo Output: khan_academy_json\
echo.

:: Run the integrated scraper
"%PYTHON_EXE%" integrated_khan_scraper.py "%1" %TIMEOUT_MINUTES%

:: Check if it ran successfully
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo SUCCESS! Questions captured successfully!
    echo ============================================================
    echo Check the khan_academy_json\ folder for captured questions
    echo.
) else (
    echo.
    echo ============================================================
    echo FAILED! Check the error messages above
    echo ============================================================
    echo.
)

echo Press any key to exit...
pause > nul