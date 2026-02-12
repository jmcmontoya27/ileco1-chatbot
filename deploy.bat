@echo off
echo ============================================
echo RAILWAY DEPLOYMENT - DIRECT UPLOAD
echo ============================================
echo.

REM Navigate to project directory
cd /d C:\FORPRODUCTION\ileco1-chatbot

echo This script will deploy directly to Railway using Railway CLI
echo.
echo OPTIONS:
echo [1] Deploy via Git (push to repository)
echo [2] Deploy directly via Railway CLI (no git required)
echo.

set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" goto git_deploy
if "%choice%"=="2" goto railway_deploy

echo Invalid choice!
pause
exit /b

:git_deploy
echo.
echo [Git Deployment] Starting...
echo.
git add requirements.txt Dockerfile
git commit -m "Fix: PyYAML 5.4.1 with Cython for Rasa compatibility"
git push origin main
echo.
echo Waiting for Railway to detect changes...
timeout /t 10 /nobreak > nul
railway logs
goto end

:railway_deploy
echo.
echo [Direct Deployment] Starting...
echo.
railway up
echo.
railway logs
goto end

:end
echo.
echo ============================================
echo DEPLOYMENT COMPLETE!
echo ============================================
pause