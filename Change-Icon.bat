@echo off
title Customize HistVault Shortcut Icon
if exist "%~dp0installer\change_icon.ps1" (
    powershell.exe -ExecutionPolicy Bypass -File "%~dp0installer\change_icon.ps1"
) else if exist "%~dp0change_icon.ps1" (
    powershell.exe -ExecutionPolicy Bypass -File "%~dp0change_icon.ps1"
) else (
    echo [ERROR] change_icon.ps1 not found.
    pause
)
