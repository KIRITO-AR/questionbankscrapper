@echo off
echo Enhanced Khan Academy Question Scraper
echo =====================================
echo.

REM Check if URL argument is provided
if "%1"=="" (
    echo Usage: run_enhanced_scraper.bat "exercise_url" [max_questions] [timeout_minutes]
    echo Example: run_enhanced_scraper.bat "https://www.khanacademy.org/math/algebra/..." 1000 60
    echo.
    pause
    exit /b 1
)

REM Set default values
set MAX_QUESTIONS=1000
set TIMEOUT_MINUTES=60

REM Use provided arguments if available
if not "%2"=="" set MAX_QUESTIONS=%2
if not "%3"=="" set TIMEOUT_MINUTES=%3

echo Target URL: %1
echo Max Questions: %MAX_QUESTIONS%
echo Timeout: %TIMEOUT_MINUTES% minutes
echo.

REM Create output directory
if not exist "khan_academy_json" mkdir khan_academy_json

echo Starting Enhanced Khan Academy Scraper...
echo.

REM Run the enhanced scraper using the virtual environment Python
D:\collage\questionbankscrapper\.venv\Scripts\python.exe enhanced_khan_scraper.py %1 %MAX_QUESTIONS% %TIMEOUT_MINUTES%

echo.
echo Script completed. Check the khan_academy_json folder for results.
pause