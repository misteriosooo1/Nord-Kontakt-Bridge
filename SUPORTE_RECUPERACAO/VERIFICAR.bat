@echo off
setlocal
cd /d "%~dp0"
title Nord Kontakt Bridge - Verificar
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0suporte.ps1" -Acao Verificar -Destino "%~1"
echo.
pause
