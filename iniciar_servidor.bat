@echo off
title Servidor ViajaYa Frontera - En Ejecucion
color 0A
echo ====================================================
echo   INICIANDO SERVIDOR DE TRANSPORTE FRONTERIZO
echo   Saltos del Guaira - Guaira - Mundo Novo - Katuete
echo ====================================================
echo.
cd /d "%~dp0backend"
echo Iniciando servidor Django en http://127.0.0.1:8000 ...
start "" http://127.0.0.1:8000/dashboard/
python manage.py runserver 0.0.0.0:8000
pause
