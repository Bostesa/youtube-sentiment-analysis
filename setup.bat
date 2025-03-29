@echo off
echo ===== YouTube Sentiment Analysis App Setup =====
echo.

REM Create necessary directories
if not exist backend\scraper\output mkdir backend\scraper\output
if not exist backend\sentiment_analysis\models mkdir backend\sentiment_analysis\models

REM Request YouTube API key
set /p api_key="Please enter your YouTube Data API key: "

REM Save the API key to the required file
echo %api_key% > backend\scraper\api_key.txt
echo API key saved to backend\scraper\api_key.txt

REM Set up sample country codes
echo US > backend\scraper\country_codes.txt
echo Sample country code (US) added to country_codes.txt

echo.
echo Setup complete! You can now run the application with:
echo docker-compose up -d
echo.
echo Access the application at: http://localhost
pause