@echo off
:: Watchdog del HuelleroBridge — corre cada 3 minutos por Task Scheduler.
::
:: Si el proceso esta vivo no hace nada y sale. Si no esta, lo relanza y deja la
:: linea en watchdog.log. Ese log es el dato que hoy no existe: dice CUANTAS veces
:: y A QUE HORA se cae, que es lo que hace falta para saber si el bridge esta
:: crasheando de verdad o si simplemente el PC se reinicio.
::
:: No se ejecuta directo: lo lanza watchdog.vbs para que no parpadee una consola
:: cada 3 minutos sobre la pantalla de recepcion.
setlocal

set "DIR=C:\JainSportBox\HuelleroBridge"
set "EXE=%DIR%\HuelleroBridge.exe"
set "LOG=%DIR%\watchdog.log"

:: `tasklist /fi` devuelve errorlevel 0 aunque no encuentre nada (imprime "INFO:
:: No tasks are running..."), asi que el que decide es el `find`.
tasklist /fi "IMAGENAME eq HuelleroBridge.exe" | find /i "HuelleroBridge.exe" >nul
if not errorlevel 1 exit /b 0

if not exist "%EXE%" (
    echo [%date% %time%] ERROR: no existe %EXE% >> "%LOG%"
    exit /b 1
)

echo [%date% %time%] Bridge caido - relanzando >> "%LOG%"
start "" "%EXE%"
exit /b 0
