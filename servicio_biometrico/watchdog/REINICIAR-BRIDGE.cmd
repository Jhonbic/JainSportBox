@echo off
setlocal
title Reiniciar huellero - JainSportBox

:: Reinicio del huellero con doble clic, para recepcion.
::
:: Vive en la carpeta del watchdog porque lo instala el mismo .cmd: son las dos
:: herramientas de operacion del bridge y no tiene sentido un tercer instalador.
::
:: Auto-elevacion: el bridge corre como administrador (necesita el driver USB), y
:: matar un proceso elevado desde una consola normal no se puede.
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo.
echo  ============================================
echo   Reiniciando el huellero...
echo  ============================================
echo.

echo [1/3] Deteniendo el proceso actual...
taskkill /f /im HuelleroBridge.exe >nul 2>&1

:: La pausa no es de cortesia: al morir, el proceso tarda un instante en soltar los
:: puertos 8001 y 8765 y el COM del Arduino. Sin esperar, la instancia nueva los
:: encuentra tomados y se cae al arrancar — el sintoma seria "lo reinicie y ahora no
:: funciona", que es peor que no haberlo tocado.
timeout /t 3 /nobreak >nul

echo [2/3] Arrancando de nuevo...
:: Por la tarea programada y no con `start`: la tarea ya esta configurada con
:: /rl highest y el contexto correcto, asi que es el mismo arranque de siempre.
schtasks /run /tn "HuelleroBridge" >nul 2>&1
if errorlevel 1 (
    echo   La tarea programada no respondio, lanzando el exe directo...
    start "" "C:\JainSportBox\HuelleroBridge\HuelleroBridge.exe"
)

timeout /t 6 /nobreak >nul

echo [3/3] Verificando...
:: No alcanza con que el proceso exista: lo que importa es que la API responda,
:: porque "proceso vivo pero mudo" es justamente el modo de falla dificil de ver.
curl -s -m 5 http://localhost:8001/status >nul 2>&1
if not errorlevel 1 (
    echo.
    echo  LISTO: el huellero esta corriendo y responde.
    goto :fin
)

tasklist /fi "IMAGENAME eq HuelleroBridge.exe" | find /i "HuelleroBridge.exe" >nul
if not errorlevel 1 (
    echo.
    echo  ATENCION: el proceso arranco pero la API todavia no responde.
    echo  Espera unos segundos y abri http://localhost:8001/status
    goto :fin
)

echo.
echo  ERROR: no arranco. Revisa el final del log:
echo    C:\JainSportBox\HuelleroBridge\bridge.log

:fin
echo.
pause
