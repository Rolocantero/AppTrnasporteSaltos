@echo off
title Generador de APKs - ViajaYa Frontera
echo ===================================================
echo   COMPILADOR DE APKs PARA PASAJEROS Y CONDUCTORES
echo ===================================================
echo.
echo 1. Preparando codigo fuente de las aplicaciones...
python prepare_apk.py

echo.
echo 2. Agregando plataforma Android a Pasajeros...
cd android_pasajero
call npx cordova platform add android
cd ..

echo.
echo 3. Agregando plataforma Android a Conductores...
cd android_conductor
call npx cordova platform add android
cd ..

echo.
echo ===================================================
echo ARCHIVOS PROYECTO ANDROID LISTOS PARA SER COMPILADOS
echo ===================================================
echo - Proyecto Pasajero: %CD%\android_pasajero
echo - Proyecto Conductor: %CD%\android_conductor
echo ===================================================
pause
