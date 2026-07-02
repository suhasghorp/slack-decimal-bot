@echo off
REM Windows batch script to run the Slack Decimal Bot
REM Designed for Windows Task Scheduler

REM Change to script directory
cd /d "%~dp0"

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Creating...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
)

REM Run the bot
python app.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo Bot exited with error code %errorlevel%
    pause
)

