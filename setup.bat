@echo off
echo ====================================================
echo   Instagram Bot - One-Click Setup
echo ====================================================
echo.
echo Creating virtual environment...
python -m venv venv
echo.
echo Installing dependencies...
venv\Scripts\pip install -r requirements.txt --quiet
echo.
echo ====================================================
echo   Setup complete! Run: venv\Scripts\python bot.py
echo ====================================================
pause
