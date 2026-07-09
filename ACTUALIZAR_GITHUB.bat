@echo off
cd /d "%~dp0"
echo.
echo === Agente Pulse 14: subir cambios a GitHub ===
echo.
git status
echo.
set /p MSG=Mensaje del commit: 
if "%MSG%"=="" set MSG=Motor real de contornos

git add .
git commit -m "%MSG%"
git push origin main

echo.
echo Si no hay errores, espera 1-3 minutos y recarga Hugging Face.
pause
