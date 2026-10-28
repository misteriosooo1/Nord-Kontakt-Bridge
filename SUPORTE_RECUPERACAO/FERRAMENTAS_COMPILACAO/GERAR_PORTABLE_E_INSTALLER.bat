@echo off
setlocal
cd /d "%~dp0..\.."
title Nord Kontakt Bridge - Portable e Instalador
where py >nul 2>&1
if not errorlevel 1 (
    py -3 "SUPORTE_RECUPERACAO\FERRAMENTAS_COMPILACAO\build_windows.py" ambos
) else (
    python "SUPORTE_RECUPERACAO\FERRAMENTAS_COMPILACAO\build_windows.py" ambos
)
if errorlevel 1 (
    echo.
    echo FALHA: confira a mensagem acima.
    echo O instalador exige Inno Setup 6 instalado no Windows.
    echo Download oficial: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)
echo.
echo Compilacao concluida. Os executaveis estao em dist\.
explorer "%cd%\dist"
pause
