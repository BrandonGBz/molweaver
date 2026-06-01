# Quickstart

This guide renders a public structure with the local API.

## 1. Install the project

Use the platform guide that matches your system:

- [Windows](installation-windows.md)
- [Linux/macOS](installation-unix.md)

## 2. Start the server

Open the docs at:

```text
http://127.0.0.1:8010/docs
```

## 3. Test health

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8010/health"
```

## 4. Render 1GYC

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
