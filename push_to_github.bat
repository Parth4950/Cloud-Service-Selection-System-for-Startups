@echo off
REM Push Cloud Service Selection System to GitHub using Git for Windows
REM Run this from the project folder (e.g. double-click or: push_to_github.bat)

set "GIT_EXE="
if exist "C:\Program Files\Git\bin\git.exe" set "GIT_EXE=C:\Program Files\Git\bin\git.exe"
if exist "C:\Program Files (x86)\Git\bin\git.exe" set "GIT_EXE=C:\Program Files (x86)\Git\bin\git.exe"
if "%GIT_EXE%"=="" (
    echo Git not found. Please install Git for Windows or add Git to PATH.
    pause
    exit /b 1
)

cd /d "%~dp0"

if not exist ".git" (
    echo Initializing git repository...
    "%GIT_EXE%" init
    "%GIT_EXE%" remote add origin https://github.com/Parth4950/Cloud-Service-Selection-System-for-Startups.git
) else (
    "%GIT_EXE%" remote get-url origin 2>nul
    if errorlevel 1 "%GIT_EXE%" remote add origin https://github.com/Parth4950/Cloud-Service-Selection-System-for-Startups.git
)

echo Adding all files...
"%GIT_EXE%" add .

echo Committing...
"%GIT_EXE%" commit -m "Cloud Service Selection System - Flask API, frontend, Docker" 2>nul
if errorlevel 1 (
    echo No changes to commit, or commit failed. Trying push...
) else (
    echo Commit done.
)

"%GIT_EXE%" branch -M main 2>nul
echo Pushing to origin main...
"%GIT_EXE%" push -u origin main

if errorlevel 1 (
    echo.
    echo If push failed: check your GitHub login. You may need to enter credentials
    echo or use a Personal Access Token instead of password.
    echo See: https://github.com/settings/tokens
)
pause
