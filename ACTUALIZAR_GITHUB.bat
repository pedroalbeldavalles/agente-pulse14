@echo off
cd /d "C:\Users\pav09\Documents\CHAT GPT\AGENTE PULSE14\REPOSITORIO\agente-pulse14"
echo.
echo Revisando cambios...
git status
echo.
git add .
git commit -m "Biblioteca visual de motivos v3"
git push origin main
echo.
echo Proceso terminado. Revisa si hay errores encima de esta linea.
pause
