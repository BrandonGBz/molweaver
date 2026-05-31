$ErrorActionPreference = "Stop"

$ApiDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ApiDir ".venv\Scripts\python.exe"

if (!(Test-Path -LiteralPath $Python)) {
    py -3 -m venv (Join-Path $ApiDir ".venv")
    & $Python -m pip install --upgrade pip
    & $Python -m pip install -r (Join-Path $ApiDir "requirements.txt")
}

Set-Location $ApiDir
$HostName = if ($env:PYMOL_API_HOST) { $env:PYMOL_API_HOST } else { "127.0.0.1" }
$Port = if ($env:PYMOL_API_PORT) { $env:PYMOL_API_PORT } else { "8010" }
& $Python -m uvicorn app:app --host $HostName --port $Port
