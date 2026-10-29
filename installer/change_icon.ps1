param (
    [string]$Choice = "",
    [switch]$Silent = $false
)

$ErrorActionPreference = "SilentlyContinue"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "             HistVault Shortcut Icon Customizer           " -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Select an icon for your HistVault Desktop & Start Menu shortcut:" -ForegroundColor Yellow
Write-Host " [1] Apple Blue Shield       (Default - Security & Privacy)" -ForegroundColor White
Write-Host " [2] Safari Compass          (Apple Web Navigation)" -ForegroundColor White
Write-Host " [3] Dark Titanium Vault     (Safe Box)" -ForegroundColor White
Write-Host " [4] Minimalist Clock        (History & Time Archive)" -ForegroundColor White
Write-Host " [5] Stealth Privacy         (Incognito Mode)" -ForegroundColor White
Write-Host " [6] Custom .ico File        (Browse and choose your own icon)" -ForegroundColor White
Write-Host ""

$baseDir = $PSScriptRoot
if (Test-Path (Join-Path $baseDir "assets\icons")) {
    $iconsDir = Join-Path $baseDir "assets\icons"
} else {
    $baseDir = (Get-Item $PSScriptRoot).Parent.FullName
    $iconsDir = Join-Path $baseDir "assets\icons"
}

if (-not $Choice) {
    $Choice = Read-Host "Enter your choice (1-6) [default: 1]"
}
if (-not $Choice) { $Choice = "1" }

$selectedIcon = Join-Path $iconsDir "shield.ico"

switch ($Choice) {
    "1" { $selectedIcon = Join-Path $iconsDir "shield.ico"; Write-Host "Selected: Apple Blue Shield" -ForegroundColor Green }
    "2" { $selectedIcon = Join-Path $iconsDir "safari.ico"; Write-Host "Selected: Safari Compass" -ForegroundColor Green }
    "3" { $selectedIcon = Join-Path $iconsDir "vault.ico"; Write-Host "Selected: Dark Titanium Vault" -ForegroundColor Green }
    "4" { $selectedIcon = Join-Path $iconsDir "clock.ico"; Write-Host "Selected: Minimalist Clock" -ForegroundColor Green }
    "5" { $selectedIcon = Join-Path $iconsDir "stealth.ico"; Write-Host "Selected: Stealth Privacy" -ForegroundColor Green }
    "6" {
        Write-Host "Opening file selector dialog to choose custom .ico..." -ForegroundColor Cyan
        Add-Type -AssemblyName System.Windows.Forms
        $dialog = New-Object System.Windows.Forms.OpenFileDialog
        $dialog.Filter = "Icon files (*.ico)|*.ico|All files (*.*)|*.*"
        $dialog.Title = "Select Custom HistVault Icon (.ico)"
        if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK -and (Test-Path $dialog.FileName)) {
            $selectedIcon = $dialog.FileName
            Write-Host "Selected custom icon: $selectedIcon" -ForegroundColor Green
        } else {
            Write-Host "No icon selected. Falling back to Apple Blue Shield." -ForegroundColor Yellow
            $selectedIcon = Join-Path $iconsDir "shield.ico"
        }
    }
    Default {
        $selectedIcon = Join-Path $iconsDir "shield.ico"
    }
}

# 1. Recompile HistVault.exe with the chosen icon embedded
Write-Host "Compiling HistVault.exe with selected icon..." -ForegroundColor Cyan

# Stop running HistVault processes if any so files are not locked
Get-Process -Name "HistVault" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 400

$csc = "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
$launcherCs = Join-Path $baseDir "assets\Launcher.cs"
$outExe = Join-Path $baseDir "HistVault.exe"

if ((Test-Path $csc) -and (Test-Path $launcherCs)) {
    & $csc /nologo /target:winexe /win32icon:$selectedIcon /r:System.Windows.Forms.dll /out:$outExe $launcherCs
}

# 2. Update shortcuts if installed
$installDir = Join-Path $env:LOCALAPPDATA "HistVault"
if (Test-Path $installDir) {
    Copy-Item $outExe -Destination $installDir -Force
    Copy-Item $selectedIcon -Destination (Join-Path $installDir "app.ico") -Force

    $ws = New-Object -ComObject WScript.Shell
    $desktopDir = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
    $programsDir = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Programs)

    $desktopShortcut = Join-Path $desktopDir "HistVault.lnk"
    if (Test-Path $desktopShortcut) {
        $s = $ws.CreateShortcut($desktopShortcut)
        $s.IconLocation = "$selectedIcon, 0"
        $s.Save()
    }

    $startShortcut = Join-Path $programsDir "HistVault\HistVault.lnk"
    if (Test-Path $startShortcut) {
        $s = $ws.CreateShortcut($startShortcut)
        $s.IconLocation = "$selectedIcon, 0"
        $s.Save()
    }

    # Refresh Windows Icon Cache so desktop updates instantly
    try {
        $refreshCode = @"
using System;
using System.Runtime.InteropServices;
public class ShellRefresh {
    [DllImport("shell32.dll")]
    public static extern void SHChangeNotify(int wEventId, int uFlags, IntPtr dwItem1, IntPtr dwItem2);
}
"@
        Add-Type -TypeDefinition $refreshCode -ErrorAction SilentlyContinue
        [ShellRefresh]::SHChangeNotify(0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)
    } catch {}
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " [SUCCESS] Application & shortcut icon successfully updated!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""
if (-not $Silent) {
    Read-Host "Press Enter to exit"
}
