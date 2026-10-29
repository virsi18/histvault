@echo off
title Register HistVault at Windows Startup
echo ========================================================
echo Adding HistVault Silent Watcher to Windows Startup...
echo ========================================================

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([System.IO.Path]::Combine($env:APPDATA, 'Microsoft\Windows\Start Menu\Programs\Startup', 'HistVaultWatcher.lnk')); $s.TargetPath = 'wscript.exe'; $s.Arguments = '\"%~dp0scripts\run_silent.vbs\"'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'HistVault Silent Browser History Watcher'; $s.Save()"

echo.
echo [SUCCESS] HistVault will now start automatically whenever your PC boots up.
echo All browsing history will be continuously archived in the background.
echo.
pause
