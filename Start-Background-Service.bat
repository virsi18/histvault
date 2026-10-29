@echo off
title Start HistVault Background Watcher
echo ========================================================
echo Starting HistVault Background Auto-Preservation Service
echo ========================================================
wscript.exe "%~dp0scripts\run_silent.vbs"
echo.
echo [ACTIVE] HistVault is now monitoring browser history silently.
echo Any new browsing history is automatically preserved every 30 seconds.
echo You do NOT need to keep any window open.
echo.
pause
