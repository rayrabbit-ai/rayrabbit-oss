@echo off
:: =========================================================================
:: RayRabbit OSS - Bootstrap Zero-Friction para Windows
:: Este script es un wrapper que invoca la lógica avanzada de PowerShell.
:: Permite al usuario hacer "Doble Clic" para instalar todo el ecosistema.
:: =========================================================================

echo Iniciando instalador de desarrollo de RayRabbit...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_dev.ps1"
pause
