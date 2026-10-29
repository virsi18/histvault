param (
    [switch]$LaunchAfter = $false,
    [switch]$Silent = $false
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "             HistVault Windows Installer                  " -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

$sourceDir = (Get-Item $PSScriptRoot).Parent.FullName
$installDir = Join-Path $env:LOCALAPPDATA "HistVault"

Write-Host "1. Verifying Python runtime..." -ForegroundColor Cyan
try {
    $pyVer = & py --version
    Write-Host "   Found: $pyVer" -ForegroundColor Green
} catch {
    Write-Host "   [ERROR] Python is not installed or not in PATH. Please install Python 3.9+ first." -ForegroundColor Red
    exit 1
}

Write-Host "2. Creating destination directory at:" -ForegroundColor Cyan
Write-Host "   $installDir" -ForegroundColor White
if (Test-Path $installDir) {
    Remove-Item -Path $installDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $installDir -Force | Out-Null

Write-Host "3. Copying HistVault application files..." -ForegroundColor Cyan
# Copy core application
Copy-Item -Path (Join-Path $sourceDir "histvault") -Destination $installDir -Recurse -Force
Copy-Item -Path (Join-Path $sourceDir "scripts") -Destination $installDir -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item -Path (Join-Path $sourceDir "run_desktop.py") -Destination $installDir -Force
Copy-Item -Path (Join-Path $sourceDir "HistVault-Desktop.bat") -Destination $installDir -Force
Copy-Item -Path (Join-Path $sourceDir "installer\uninstall.ps1") -Destination $installDir -Force

# Create launch_silent.vbs in install directory
$vbsScript = @"
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strDir
WshShell.Run "py run_desktop.py", 0, False
Set WshShell = Nothing
Set fso = Nothing
"@
Set-Content -Path (Join-Path $installDir "launch_silent.vbs") -Value $vbsScript -Force

# Create uninstall.bat in install directory
$uninstallBat = @"
@echo off
title Uninstall HistVault
powershell.exe -ExecutionPolicy Bypass -File "%~dp0uninstall.ps1"
"@
Set-Content -Path (Join-Path $installDir "uninstall.bat") -Value $uninstallBat -Force

Write-Host "4. Creating Desktop and Start Menu shortcuts..." -ForegroundColor Cyan
$ws = New-Object -ComObject WScript.Shell

$desktopDir = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$programsDir = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Programs)

# Desktop Shortcut (if desktop directory exists)
if (Test-Path $desktopDir) {
    $desktopShortcutPath = Join-Path $desktopDir "HistVault.lnk"
    $shortcut = $ws.CreateShortcut($desktopShortcutPath)
    $shortcut.TargetPath = "wscript.exe"
    $shortcut.Arguments = "`"$installDir\launch_silent.vbs`""
    $shortcut.WorkingDirectory = $installDir
    $shortcut.Description = "HistVault - Browser History Preservation Archive"
    $shortcut.Save()
}

# Start Menu Folder
$startMenuDir = Join-Path $programsDir "HistVault"
New-Item -ItemType Directory -Path $startMenuDir -Force | Out-Null

# Start Menu App Shortcut
$startAppShortcut = $ws.CreateShortcut((Join-Path $startMenuDir "HistVault.lnk"))
$startAppShortcut.TargetPath = "wscript.exe"
$startAppShortcut.Arguments = "`"$installDir\launch_silent.vbs`""
$startAppShortcut.WorkingDirectory = $installDir
$startAppShortcut.Description = "HistVault - Browser History Preservation Archive"
$startAppShortcut.Save()

# Start Menu Uninstall Shortcut
$startUninstallShortcut = $ws.CreateShortcut((Join-Path $startMenuDir "Uninstall HistVault.lnk"))
$startUninstallShortcut.TargetPath = "cmd.exe"
$startUninstallShortcut.Arguments = "/c `"`"$installDir\uninstall.bat`"`""
$startUninstallShortcut.WorkingDirectory = $installDir
$startUninstallShortcut.Description = "Uninstall HistVault and wipe all history database"
$startUninstallShortcut.Save()

Write-Host "5. Registering in Windows Settings (Apps > Installed apps)..." -ForegroundColor Cyan
$regKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\HistVault"
New-Item -Path $regKey -Force | Out-Null
Set-ItemProperty -Path $regKey -Name "DisplayName" -Value "HistVault" -Force
Set-ItemProperty -Path $regKey -Name "DisplayVersion" -Value "1.0.0" -Force
Set-ItemProperty -Path $regKey -Name "Publisher" -Value "HistVault Open Source Project" -Force
Set-ItemProperty -Path $regKey -Name "InstallLocation" -Value $installDir -Force
Set-ItemProperty -Path $regKey -Name "UninstallString" -Value "cmd.exe /c `"`"$installDir\uninstall.bat`"`"" -Force
Set-ItemProperty -Path $regKey -Name "Comments" -Value "Automated Browser History Preservation Vault & Anti-Deletion Archive" -Force
Set-ItemProperty -Path $regKey -Name "NoModify" -Value 1 -Type DWord -Force
Set-ItemProperty -Path $regKey -Name "NoRepair" -Value 1 -Type DWord -Force

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " [SUCCESS] HistVault installed successfully!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""
Write-Host " * Desktop Shortcut created:      Desktop\HistVault.lnk" -ForegroundColor White
Write-Host " * Start Menu entry added:        Programs\HistVault" -ForegroundColor White
Write-Host " * Registered in Windows Settings: Apps > Installed apps" -ForegroundColor White
Write-Host ""

if ($LaunchAfter) {
    Write-Host "Launching HistVault Desktop Application..." -ForegroundColor Cyan
    Start-Process "wscript.exe" -ArgumentList "`"$installDir\launch_silent.vbs`"" -WorkingDirectory $installDir
} elseif (-not $Silent) {
    Read-Host "Press Enter to finish installation"
}
