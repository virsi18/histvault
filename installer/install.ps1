param (
    [switch]$LaunchAfter = $false,
    [switch]$Silent = $false,
    [string]$IconChoice = "1"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "             HistVault Windows Installer                  " -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

$sourceDir = (Get-Item $PSScriptRoot).Parent.FullName
$installDir = Join-Path $env:LOCALAPPDATA "HistVault"
$iconsDir = Join-Path $sourceDir "assets\icons"

Write-Host "1. Verifying Python runtime..." -ForegroundColor Cyan
try {
    $pyVer = & py --version
    Write-Host "   Found: $pyVer" -ForegroundColor Green
} catch {
    Write-Host "   [ERROR] Python is not installed or not in PATH. Please install Python 3.9+ first." -ForegroundColor Red
    exit 1
}

# Icon Selection
$selectedIcon = Join-Path $iconsDir "shield.ico"

if (-not $Silent) {
    Write-Host ""
    Write-Host "Choose your preferred Desktop & Start Menu shortcut icon:" -ForegroundColor Yellow
    Write-Host " [1] Apple Blue Shield       (Default - Security & Privacy)" -ForegroundColor White
    Write-Host " [2] Safari Compass          (Apple Web Navigation)" -ForegroundColor White
    Write-Host " [3] Dark Titanium Vault     (Safe Box)" -ForegroundColor White
    Write-Host " [4] Minimalist Clock        (History & Time Archive)" -ForegroundColor White
    Write-Host " [5] Stealth Privacy         (Incognito Mode)" -ForegroundColor White
    Write-Host " [6] Custom .ico File        (Browse and choose your own icon)" -ForegroundColor White
    Write-Host ""
    $userChoice = Read-Host "Enter icon choice (1-6) [default: 1]"
    if ($userChoice) { $IconChoice = $userChoice }
}

switch ($IconChoice) {
    "1" { $selectedIcon = Join-Path $iconsDir "shield.ico"; Write-Host "   Selected icon: Apple Blue Shield" -ForegroundColor Green }
    "2" { $selectedIcon = Join-Path $iconsDir "safari.ico"; Write-Host "   Selected icon: Safari Compass" -ForegroundColor Green }
    "3" { $selectedIcon = Join-Path $iconsDir "vault.ico"; Write-Host "   Selected icon: Dark Titanium Vault" -ForegroundColor Green }
    "4" { $selectedIcon = Join-Path $iconsDir "clock.ico"; Write-Host "   Selected icon: Minimalist Clock" -ForegroundColor Green }
    "5" { $selectedIcon = Join-Path $iconsDir "stealth.ico"; Write-Host "   Selected icon: Stealth Privacy" -ForegroundColor Green }
    "6" {
        Write-Host "   Opening file picker for custom .ico..." -ForegroundColor Cyan
        Add-Type -AssemblyName System.Windows.Forms
        $dialog = New-Object System.Windows.Forms.OpenFileDialog
        $dialog.Filter = "Icon files (*.ico)|*.ico|All files (*.*)|*.*"
        $dialog.Title = "Select Custom HistVault Icon (.ico)"
        if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK -and (Test-Path $dialog.FileName)) {
            $selectedIcon = $dialog.FileName
            Write-Host "   Selected custom icon: $selectedIcon" -ForegroundColor Green
        } else {
            Write-Host "   No icon chosen. Using default Apple Blue Shield." -ForegroundColor Yellow
            $selectedIcon = Join-Path $iconsDir "shield.ico"
        }
    }
    Default {
        $selectedIcon = Join-Path $iconsDir "shield.ico"
        Write-Host "   Selected default icon: Apple Blue Shield" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "2. Compiling native HistVault.exe executable..." -ForegroundColor Cyan
$csc = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
$launcherCs = Join-Path $sourceDir "assets\Launcher.cs"
$compiledExe = Join-Path $sourceDir "HistVault.exe"

if ((Test-Path $csc) -and (Test-Path $launcherCs)) {
    & $csc /nologo /target:winexe /win32icon:$selectedIcon /r:System.Windows.Forms.dll /out:$compiledExe $launcherCs
    Write-Host "   [SUCCESS] Compiled native HistVault.exe with embedded icon!" -ForegroundColor Green
} else {
    Write-Host "   [NOTICE] C# compiler not found. Using script launcher fallback." -ForegroundColor Yellow
}

Write-Host "3. Creating destination directory at:" -ForegroundColor Cyan
Write-Host "   $installDir" -ForegroundColor White
if (Test-Path $installDir) {
    Remove-Item -Path $installDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $installDir -Force | Out-Null

Write-Host "4. Installing HistVault application files..." -ForegroundColor Cyan
Copy-Item -Path (Join-Path $sourceDir "histvault") -Destination $installDir -Recurse -Force
Copy-Item -Path (Join-Path $sourceDir "assets") -Destination $installDir -Recurse -Force
Copy-Item -Path (Join-Path $sourceDir "scripts") -Destination $installDir -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item -Path (Join-Path $sourceDir "run_desktop.py") -Destination $installDir -Force
Copy-Item -Path (Join-Path $sourceDir "HistVault.exe") -Destination $installDir -Force
Copy-Item -Path (Join-Path $sourceDir "Change-Icon.bat") -Destination $installDir -Force
Copy-Item -Path (Join-Path $sourceDir "installer\uninstall.ps1") -Destination $installDir -Force
Copy-Item -Path (Join-Path $sourceDir "installer\change_icon.ps1") -Destination (Join-Path $installDir "change_icon.ps1") -Force
Copy-Item -Path $selectedIcon -Destination (Join-Path $installDir "app.ico") -Force

# Create uninstall.bat in install directory
$uninstallBat = @"
@echo off
title Uninstall HistVault
powershell.exe -ExecutionPolicy Bypass -File "%~dp0uninstall.ps1"
"@
Set-Content -Path (Join-Path $installDir "uninstall.bat") -Value $uninstallBat -Force

Write-Host "5. Creating Desktop and Start Menu shortcuts with your icon..." -ForegroundColor Cyan
$ws = New-Object -ComObject WScript.Shell

$desktopDir = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$programsDir = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Programs)

$exePath = Join-Path $installDir "HistVault.exe"
$icoPath = Join-Path $installDir "app.ico"

# Desktop Shortcut
if (Test-Path $desktopDir) {
    $desktopShortcutPath = Join-Path $desktopDir "HistVault.lnk"
    $shortcut = $ws.CreateShortcut($desktopShortcutPath)
    $shortcut.TargetPath = $exePath
    $shortcut.WorkingDirectory = $installDir
    $shortcut.IconLocation = "$icoPath, 0"
    $shortcut.Description = "HistVault - Browser History Preservation Archive"
    $shortcut.Save()
}

# Start Menu Folder
$startMenuDir = Join-Path $programsDir "HistVault"
New-Item -ItemType Directory -Path $startMenuDir -Force | Out-Null

# Start Menu App Shortcut
$startAppShortcut = $ws.CreateShortcut((Join-Path $startMenuDir "HistVault.lnk"))
$startAppShortcut.TargetPath = $exePath
$startAppShortcut.WorkingDirectory = $installDir
$startAppShortcut.IconLocation = "$icoPath, 0"
$startAppShortcut.Description = "HistVault - Browser History Preservation Archive"
$startAppShortcut.Save()

# Start Menu Change Icon Shortcut
$changeIconShortcut = $ws.CreateShortcut((Join-Path $startMenuDir "Change Shortcut Icon.lnk"))
$changeIconShortcut.TargetPath = "cmd.exe"
$changeIconShortcut.Arguments = "/c `"`"$installDir\Change-Icon.bat`"`""
$changeIconShortcut.WorkingDirectory = $installDir
$changeIconShortcut.IconLocation = "$icoPath, 0"
$changeIconShortcut.Description = "Change the shortcut icon for HistVault"
$changeIconShortcut.Save()

# Start Menu Uninstall Shortcut
$startUninstallShortcut = $ws.CreateShortcut((Join-Path $startMenuDir "Uninstall HistVault.lnk"))
$startUninstallShortcut.TargetPath = "cmd.exe"
$startUninstallShortcut.Arguments = "/c `"`"$installDir\uninstall.bat`"`""
$startUninstallShortcut.WorkingDirectory = $installDir
$startUninstallShortcut.Description = "Uninstall HistVault and wipe all history database"
$startUninstallShortcut.Save()

Write-Host "6. Registering in Windows Settings (Apps > Installed apps)..." -ForegroundColor Cyan
$regKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\HistVault"
New-Item -Path $regKey -Force | Out-Null
Set-ItemProperty -Path $regKey -Name "DisplayName" -Value "HistVault" -Force
Set-ItemProperty -Path $regKey -Name "DisplayVersion" -Value "1.0.0" -Force
Set-ItemProperty -Path $regKey -Name "Publisher" -Value "HistVault Open Source Project" -Force
Set-ItemProperty -Path $regKey -Name "InstallLocation" -Value $installDir -Force
Set-ItemProperty -Path $regKey -Name "DisplayIcon" -Value "$exePath,0" -Force
Set-ItemProperty -Path $regKey -Name "UninstallString" -Value "cmd.exe /c `"`"$installDir\uninstall.bat`"`"" -Force
Set-ItemProperty -Path $regKey -Name "Comments" -Value "Automated Browser History Preservation Vault & Anti-Deletion Archive" -Force
Set-ItemProperty -Path $regKey -Name "NoModify" -Value 1 -Type DWord -Force
Set-ItemProperty -Path $regKey -Name "NoRepair" -Value 1 -Type DWord -Force

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " [SUCCESS] HistVault installed successfully!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""
Write-Host " * Standalone Executable:         $exePath" -ForegroundColor White
Write-Host " * Desktop Shortcut created:      Desktop\HistVault.lnk (Custom Icon)" -ForegroundColor White
Write-Host " * Start Menu entry added:        Programs\HistVault" -ForegroundColor White
Write-Host " * Change Icon Utility:           Start Menu > Change Shortcut Icon" -ForegroundColor White
Write-Host " * Registered in Windows Settings: Apps > Installed apps" -ForegroundColor White
Write-Host ""

if ($LaunchAfter) {
    Write-Host "Launching HistVault Native Executable..." -ForegroundColor Cyan
    Start-Process $exePath -WorkingDirectory $installDir
} elseif (-not $Silent) {
    Read-Host "Press Enter to finish installation"
}
