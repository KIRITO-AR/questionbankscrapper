@echo off
REM Direct Khan Academy Scraper - No SSL Issues
REM This script runs the direct scraper that bypasses proxy SSL problems

echo.
echo ================================================
echo  Direct Khan Academy Question Scraper
echo ================================================
echo.
echo This tool captures Perseus JSON data directly from Khan Academy exercises
echo without using a proxy, eliminating SSL certificate issues.
echo.
echo Usage examples:
echo   run_direct.bat
echo   run_direct.bat "https://www.khanacademy.org/math/algebra/..."
echo   run_direct.bat "https://www.khanacademy.org/math/algebra/..." 10
echo.

REM Set default values
set DEFAULT_URL=https://www.khanacademy.org/math/basic-geo/basic-geo-angles/measuring-angles/e/angle_types
set DEFAULT_COUNT=5

REM Use provided arguments or defaults
set TARGET_URL=%~1
set QUESTION_COUNT=%~2

if "%TARGET_URL%"=="" set TARGET_URL=%DEFAULT_URL%
if "%QUESTION_COUNT%"=="" set QUESTION_COUNT=%DEFAULT_COUNT%

echo Target URL: %TARGET_URL%
echo Max questions: %QUESTION_COUNT%
echo Save directory: khan_academy_json
echo.
echo ================================================
echo Starting direct scraper...
echo ================================================

REM Run the direct scraper
.venv\Scripts\python.exe direct_scraper.py "%TARGET_URL%" %QUESTION_COUNT%

echo.
echo ================================================
echo Scraping complete!
echo ================================================
echo.
echo Captured questions are saved in: khan_academy_json\
echo.
pause