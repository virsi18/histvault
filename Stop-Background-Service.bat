@echo off
title Stop HistVault Background Watcher
echo Stopping HistVault background service...
powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*histvault.cli.main watch*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo [STOPPED] Background watcher service has been terminated.
pause
