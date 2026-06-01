param(
    [switch]$Start,
    [int]$Port = 8010
)

$ErrorActionPreference = "Stop"

$ApiDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ApiDir

function Write-Section([string]$Message) {
    Write-Host ""
    Write-Host $Message
}

function Get-PythonLauncher {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return @{ Command = "py"; Args = @("-3") }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @{ Command = $python.Source; Args = @() }
    }

    throw "No se encontro Python 3.10+. Instala Python y vuelve a ejecutar install.ps1."
}

$launcher = Get-PythonLauncher
& $launcher.Command @launcher.Args -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) {
    throw "Se requiere Python 3.10 o superior."
}

$venvPython = Join-Path $ApiDir ".venv\Scripts\python.exe"
if (!(Test-Path -LiteralPath $venvPython)) {
    Write-Section "Creating .venv..."
    & $launcher.Command @launcher.Args -m venv (Join-Path $ApiDir ".venv")
}

Write-Section "Updating pip and installing dependencies..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $ApiDir "requirements.txt")

$envFile = Join-Path $ApiDir ".env"
$envExample = Join-Path $ApiDir ".env.example"
if (!(Test-Path -LiteralPath $envFile) -and (Test-Path -LiteralPath $envExample)) {
    Write-Section "Creating .env from .env.example..."
    Copy-Item -LiteralPath $envExample -Destination $envFile
}

Write-Section "Configuring local PyMOL..."
& (Join-Path $ApiDir "setup_pymol_env.ps1")

$pymolPython = Join-Path $ApiDir "tools\pymol_env\python.exe"
if (!(Test-Path -LiteralPath $pymolPython)) {
    throw "Could not find tools\pymol_env\python.exe after the PyMOL setup completed."
}

& $pymolPython -c "import pymol2; print('PyMOL/pymol2 ready')"

Write-Section "Installation complete."
Write-Host "  API: http://127.0.0.1:$Port"
Write-Host "  Docs: http://127.0.0.1:$Port/docs"
Write-Host "  To start the server manually: .\start_server.ps1"

if ($Start) {
    Write-Section "Starting server..."
    & (Join-Path $ApiDir "start_server.ps1") -Port $Port
}
