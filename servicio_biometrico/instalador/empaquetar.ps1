# (Guardado como UTF-8 CON BOM. Sin BOM, PowerShell 5.1 lo lee como CP1252 y basta
#  un guion largo para romper el parseo: uno de sus bytes cae en la comilla
#  tipografica de cierre y termina el string antes de tiempo.)
#
# Arma el paquete de instalacion del huellero para llevar a una PC nueva.
#
# El exe SIEMPRE sale del build actual (bin\Debug\net48). Esa es la razon de ser de
# este script: el instalador que se armaba a mano quedo con un exe de un mes antes,
# apuntando a un backend que ya estaba dado de baja, y el sintoma en la PC nueva no
# era un error claro sino "el lector no reconoce a nadie".
#
# El RTE de DigitalPersona (19 MB, redistribuible de un tercero) NO esta en git: se
# copia de -RteOrigen, que por defecto apunta al paquete anterior en Downloads.
#
# Uso:
#   .\servicio_biometrico\instalador\empaquetar.ps1
#   .\servicio_biometrico\instalador\empaquetar.ps1 -Salida D:\huellero -Zip
#   .\servicio_biometrico\instalador\empaquetar.ps1 -RteOrigen C:\ruta\al\RTE
#
# Flags:
#   -Salida <ruta>     donde dejar el paquete (default: <repo>\dist\HuelleroBridge-Instalador)
#   -RteOrigen <ruta>  carpeta RTE de DigitalPersona
#   -Zip               ademas comprime el paquete en un .zip
#   -SinRte            arma el paquete sin el RTE (para una PC que ya lo tiene)

param(
    [string]$Salida,
    [string]$RteOrigen = "$env:USERPROFILE\Downloads\HuelleroBridge-Instalador\RTE",
    [switch]$Zip,
    [switch]$SinRte
)

$ErrorActionPreference = 'Stop'

$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Resolve-Path (Join-Path $aqui '..\..')
$build = Join-Path $repo 'servicio_biometrico\bin\Debug\net48'

if (-not $Salida) { $Salida = Join-Path $repo 'dist\HuelleroBridge-Instalador' }

# ── El exe tiene que existir y ser mas nuevo que los fuentes ──
$exe = Join-Path $build 'HuelleroBridge.exe'
if (-not (Test-Path $exe)) {
    throw "No existe $exe. Compila primero: dotnet build servicio_biometrico\HuelleroBridge.csproj"
}
$fuenteMasNueva = Get-ChildItem (Join-Path $repo 'servicio_biometrico') -Filter *.cs |
                  Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($fuenteMasNueva -and $fuenteMasNueva.LastWriteTime -gt (Get-Item $exe).LastWriteTime) {
    Write-Warning "$($fuenteMasNueva.Name) es mas nuevo que el exe: recompila antes de empaquetar."
    Write-Warning "  dotnet build servicio_biometrico\HuelleroBridge.csproj"
    if (-not $PSBoundParameters.ContainsKey('Salida')) { throw "Abortado para no empaquetar un exe viejo." }
}

# ── Armar ──
if (Test-Path $Salida) { Remove-Item $Salida -Recurse -Force }
New-Item -ItemType Directory -Path (Join-Path $Salida 'Bridge') -Force | Out-Null

# Solo lo que la PC necesita para correr: el exe, su config, Fleck y las 4 DLLs del
# SDK. El .pdb no va (son simbolos de depuracion).
$necesarios = @(
    'HuelleroBridge.exe', 'HuelleroBridge.exe.config', 'Fleck.dll',
    'DPFPDevNET.dll', 'DPFPEngNET.dll', 'DPFPShrNET.dll', 'DPFPVerNET.dll'
)
foreach ($f in $necesarios) {
    $origen = Join-Path $build $f
    if (-not (Test-Path $origen)) { throw "Falta $f en $build" }
    Copy-Item $origen (Join-Path $Salida 'Bridge') -Force
}

Copy-Item (Join-Path $aqui 'INSTALAR.cmd') $Salida -Force
Copy-Item (Join-Path $aqui 'LEEME.txt')    $Salida -Force

# El watchdog viaja en el mismo paquete a proposito: es un segundo instalador, pero
# el costo real de esto no es ejecutar dos .cmd sino IR hasta el gimnasio. Que se
# arme aparte garantizaria que alguna vez se instale el bridge sin watchdog.
$watchdog = Join-Path $repo 'servicio_biometrico\watchdog'
Copy-Item $watchdog (Join-Path $Salida 'Watchdog') -Recurse -Force

# El sketch del Arduino tambien: RELE_MS vive en la placa, no en el exe, asi que
# reinstalar el bridge NO cambia el tiempo que la palanquera queda abierta. Si el
# .ino no va en el paquete, ese paso se olvida y el viaje se hace de nuevo.
$sketch = Join-Path $repo 'servicio_biometrico\arduino'
Copy-Item $sketch (Join-Path $Salida 'Arduino') -Recurse -Force

if ($SinRte) {
    Write-Host "  RTE omitido (-SinRte)."
} elseif (Test-Path $RteOrigen) {
    Copy-Item $RteOrigen (Join-Path $Salida 'RTE') -Recurse -Force
    Write-Host "  RTE copiado de $RteOrigen"
} else {
    Write-Warning "No se encontro el RTE en $RteOrigen. El paquete queda sin el."
    Write-Warning "Pasa -RteOrigen (ruta) o -SinRte si la PC destino ya lo tiene."
}

# ── Resumen ──
$fecha = (Get-Item $exe).LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
$hash  = (Get-FileHash $exe -Algorithm MD5).Hash.Substring(0, 12)
# A que backend apunta el exe, leido del binario: es exactamente el dato que estaba
# mal en el paquete anterior, asi que se imprime para poder verlo antes de llevarlo.
$bytes = [IO.File]::ReadAllBytes($exe)
$txt   = [Text.Encoding]::Unicode.GetString($bytes)
# Acotado a caracteres validos de URL: el literal que sigue en el binario decodifica
# a caracteres CJK (no a \x00), asi que un [^\s\x00]* se lleva basura pegada al final.
$apunta = if ($txt -match 'https?://[A-Za-z0-9.\-]*onrender[A-Za-z0-9.\-/]*') { $Matches[0] }
          elseif ($txt -match 'https?://[A-Za-z0-9.\-]*railway[A-Za-z0-9.\-/]*') { $Matches[0] + '  <-- OJO: backend viejo' }
          else { '(no se pudo leer del binario)' }

$tam = '{0:N1} MB' -f ((Get-ChildItem $Salida -Recurse -File | Measure-Object Length -Sum).Sum / 1MB)

Write-Host ""
Write-Host "Paquete listo: $Salida"
Write-Host "  exe compilado : $fecha (md5 $hash)"
Write-Host "  apunta a      : $apunta"
Write-Host "  tamano        : $tam"

if ($Zip) {
    # OJO: no llamar a esta variable $zip. PowerShell no distingue mayusculas, asi que
    # seria la misma que el switch -Zip y asignarle un string revienta el script.
    $rutaZip = "$Salida.zip"
    if (Test-Path $rutaZip) { Remove-Item $rutaZip -Force }
    Compress-Archive -Path "$Salida\*" -DestinationPath $rutaZip
    Write-Host "  zip           : $rutaZip"
}
Write-Host ""
Write-Host "Recorda: el instalador va a pedir el BRIDGE_SECRET del backend."
