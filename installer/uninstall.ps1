param (
    [switch]$Silent = $false
)

$ErrorActionPreference = "SilentlyContinue"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "             HistVault Windows Uninstaller                " -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not $Silent) {
    Write-Host "WARNING:" -ForegroundColor Yellow
    Write-Host "Uninstalling will permanently remove:" -ForegroundColor Yellow
    Write-Host " 1. HistVault desktop application files" -ForegroundColor White
    Write-Host " 2. Desktop and Start Menu shortcuts" -ForegroundColor White
    Write-Host " 3. Background auto-watcher services" -ForegroundColor White
    Write-Host " 4. ALL PRESERVED BROWSER HISTORY DATA (~/.histvault/vault.db)" -ForegroundColor Red
    Write-Host ""
    $answer = Read-Host "Proceed with complete uninstallation and erase all history? (Y/N)"
    if ($answer -ne 'Y' -and $answer -ne 'y') {
        Write-Host "Uninstallation canceled." -ForegroundColor Gray
        exit 0
    }
}

Write-Host ""
Write-Host "1. Stopping any active HistVault processes..." -ForegroundColor Cyan
Get-CimInstance Win32_Process | Where-Object { 
    $_.ProcessId -ne $PID -and ($_.CommandLine -like "*histvault.cli.main*" -or $_.CommandLine -like "*run_desktop.py*")
} | ForEach-Object { 
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue 
}
Start-Sleep -Seconds 1

Write-Host "2. Removing shortcuts..." -ForegroundColor Cyan
$desktopDir = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$programsDir = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Programs)
$startupDir = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Startup)

# Remove Desktop shortcut
if (Test-Path $desktopDir) {
    $desktopShortcut = Join-Path $desktopDir "HistVault.lnk"
    if (Test-Path $desktopShortcut) { Remove-Item $desktopShortcut -Force }
}

# Remove Start Menu folder
$startMenuFolder = Join-Path $programsDir "HistVault"
if (Test-Path $startMenuFolder) { Remove-Item $startMenuFolder -Recurse -Force }

# Remove Startup shortcut
$startupShortcut = Join-Path $startupDir "HistVaultWatcher.lnk"
if (Test-Path $startupShortcut) { Remove-Item $startupShortcut -Force }

Write-Host "3. Erasing all preserved browser history database..." -ForegroundColor Red
$vaultDir = Join-Path $env:USERPROFILE ".histvault"
if (Test-Path $vaultDir) {
    Remove-Item -Path $vaultDir -Recurse -Force
    Write-Host "   [WIPED] Database at ~/.histvault/ has been completely deleted." -ForegroundColor Green
}

Write-Host "4. Removing Windows Registry entries..." -ForegroundColor Cyan
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\HistVault"
if (Test-Path $regPath) {
    Remove-Item -Path $regPath -Recurse -Force
}

Write-Host "5. Cleaning up installed program files..." -ForegroundColor Cyan
$installDir = Join-Path $env:LOCALAPPDATA "HistVault"
if (Test-Path $installDir) {
    # Delete installed files via background cmd to allow script to exit cleanly
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c timeout /t 1 >nul & rmdir /s /q `"$installDir`"" -WindowStyle Hidden
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " [SUCCESS] HistVault and all history have been uninstalled." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""
if (-not $Silent) {
    Read-Host "Press Enter to exit uninstaller"
}
