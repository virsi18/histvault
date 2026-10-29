@echo off
title Remove HistVault from Windows Startup
powershell -Command "Remove-Item -Path (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup\HistVaultWatcher.lnk') -Force -ErrorAction SilentlyContinue"
echo [REMOVED] HistVault removed from Windows Startup.
pause
