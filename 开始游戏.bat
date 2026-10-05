@echo off
chcp 936 >nul
title Hazard Ball
cd /d "%~dp0"
if not exist "Hazard.exe" (
    echo [¥ÌŒÛ] Œ¥’“µΩ Hazard.exe
    pause
    exit /b 1
)
start "" "Hazard.exe"
exit /b 0
