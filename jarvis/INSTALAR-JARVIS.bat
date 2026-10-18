@echo off
chcp 65001 >nul
title Instalador do Ryan
echo.
echo  ==============================================
echo   Instalador do Ryan (Hermes + Claude Code)
echo  ==============================================
echo.
echo  Vao abrir duas janelas: escolha a pasta do jogo e depois o Godot (_console.exe).
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar-windows.ps1"
echo.
echo  Se apareceu algum erro em vermelho, tire um print desta janela.
pause
