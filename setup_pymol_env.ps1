$ErrorActionPreference = "Stop"

$ApiDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ToolsDir = Join-Path $ApiDir "tools"
$Archive = Join-Path $ToolsDir "micromamba.tar.bz2"
$MicromambaDir = Join-Path $ToolsDir "micromamba"
$Micromamba = Join-Path $MicromambaDir "Library\bin\micromamba.exe"
$Root = Join-Path $ToolsDir "mamba_root"
$Prefix = Join-Path $ToolsDir "pymol_env"

New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null

if (!(Test-Path -LiteralPath $Archive)) {
    Invoke-WebRequest -Uri "https://micro.mamba.pm/api/micromamba/win-64/latest" -OutFile $Archive
}

if (!(Test-Path -LiteralPath $Micromamba)) {
    New-Item -ItemType Directory -Force -Path $MicromambaDir | Out-Null
    tar -xjf $Archive -C $MicromambaDir
}

if (!(Test-Path -LiteralPath (Join-Path $Prefix "python.exe"))) {
    & $Micromamba create -y -r $Root -p $Prefix -c conda-forge python=3.10 pymol-open-source
}

& $Micromamba run -r $Root -p $Prefix python -c "import pymol2; print('PyMOL/pymol2 ready')"
