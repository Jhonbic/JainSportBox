@echo off
setlocal
title Watchdog HuelleroBridge - JainSportBox

:: Auto-elevacion: la tarea se crea con /rl highest y eso exige admin.
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Pidiendo permisos de administrador...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"
set "DESTINO=C:\JainSportBox\HuelleroBridge"

echo.
echo  ============================================
echo   Watchdog del huellero - JainSportBox
echo  ============================================
echo.

if not exist "%DESTINO%\HuelleroBridge.exe" (
    echo  ERROR: no encuentro %DESTINO%\HuelleroBridge.exe
    echo  Instala primero el bridge con instalador\INSTALAR.cmd
    echo.
    pause
    exit /b 1
)

echo [1/3] Copiando scripts a %DESTINO% ...
copy /y "watchdog.cmd" "%DESTINO%\" >nul
copy /y "watchdog.vbs" "%DESTINO%\" >nul
echo   Listo.

:: /rl highest porque el bridge necesita permisos de administrador para hablarle al
:: driver USB del lector: si el watchdog lo relanza sin elevacion, arranca pero no
:: reconoce ninguna huella, que es un fallo mas dificil de ver que si no arrancara.
echo [2/3] Creando la tarea programada (cada 3 minutos)...
:: Una sola linea y sin comillas internas a proposito: la ruta de destino es fija y
:: no tiene espacios, asi que no hace falta escapar nada dentro de /tr — que es
:: justo donde `schtasks` se rompe de formas dificiles de leer.
schtasks /create /f /tn "HuelleroBridge Watchdog" /sc minute /mo 3 /rl highest /tr "wscript.exe C:\JainSportBox\HuelleroBridge\watchdog.vbs" >nul
if errorlevel 1 (
    echo   ERROR creando la tarea.
    pause
    exit /b 1
)
echo   Tarea "HuelleroBridge Watchdog" creada.

echo [3/3] Primera corrida de prueba...
schtasks /run /tn "HuelleroBridge Watchdog" >nul
echo   Listo.

echo.
echo  ============================================
echo   Instalado.
echo  ============================================
echo.
echo  Cada 3 minutos revisa si HuelleroBridge.exe esta corriendo y lo
echo  relanza si no. Cada relanzamiento queda registrado en:
echo    %DESTINO%\watchdog.log
echo.
echo  Ese log es el que dice si el bridge se esta cayendo de verdad.
echo  Si pasan los dias y sigue vacio, el problema no eran caidas.
echo.
echo  IMPORTANTE: el watchdog corre en la sesion del usuario, asi que NO
echo  cubre el caso de que el PC se reinicie y nadie inicie sesion. Para
echo  eso hay que activar el inicio de sesion automatico en este PC.
echo.
pause
