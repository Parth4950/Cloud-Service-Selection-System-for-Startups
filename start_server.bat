@echo off
cd /d "%~dp0"
echo Starting server from: %CD%
echo Frontend at: http://127.0.0.1:5001/
echo API docs at: http://127.0.0.1:5001/api
echo.
python run.py
pause
