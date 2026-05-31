# Quickstart

This guide renders a public structure with the local API.

## 1. Install Python dependencies

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 2. Install PyMOL

Recommended on Windows:

```powershell
.\setup_pymol_env.ps1
```

## 3. Start the server

```powershell
.\start_server.ps1
```

Open:

```text
http://127.0.0.1:8010/docs
```

## 4. Test health

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8010/health"
```

## 5. Render 1GYC

```powershell
$body = @{
  pdb_id = "1GYC"
  output_name = "1gyc_copper_sites"
  preset = "copper_sites"
  color = "chainbow"
  ray = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8010/render" -Method Post -ContentType "application/json" -Body $body
```
