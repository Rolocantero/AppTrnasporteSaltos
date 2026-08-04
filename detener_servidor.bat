@echo off
title Detener Servidor ViajaYa Frontera
color 0C
echo ====================================================
echo   DETENIENDO SERVIDOR DE TRANSPORTE FRONTERIZO
echo ====================================================
echo.
echo Deteniendo procesos de Python ejecutando el servidor...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo.
echo ====================================================
echo   ¡EL SERVIDOR HA SIDO DETENIDO CON EXITO!
echo ====================================================
echo.
pause
