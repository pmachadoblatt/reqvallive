# Bootstrap ReqValLive (Windows) — um único clone basta
# Uso: .\scripts\bootstrap.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$vendor = Join-Path $Root "vendor\Sim_Req_Validator"
if (-not (Test-Path (Join-Path $vendor "pyproject.toml"))) {
    Write-Error "Falta vendor\Sim_Req_Validator. Faça git pull no repo reqvallive."
}

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& ".\.venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -e $vendor
pip install -e ".[dev]"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Criado .env a partir de .env.example — edite MQTT_PASSWORD e LLM_API_KEY."
}

Write-Host ""
Write-Host "OK. Para subir o app:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  reqvallive"
Write-Host "Abra http://127.0.0.1:8080"
