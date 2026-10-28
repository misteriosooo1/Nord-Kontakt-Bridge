@echo off
setlocal
cd /d "%~dp0"
title Nord Kontakt Bridge - Reparar
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0suporte.ps1" -Acao Reparar -Destino "%~1"
echo.
pause
