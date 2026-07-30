# Sobe SysON + Postgres. Uso: .\deploy\syson\up.ps1
$ErrorActionPreference = "Stop"
$Here = $PSScriptRoot
Set-Location $Here

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker nao encontrado. Instale Docker Desktop e confirme que esta a correr."
}

$envFile = Join-Path $Here ".env"
if (-not (Test-Path $envFile)) {
    $example = Join-Path $Here ".env.example"
    if (Test-Path $example) {
        Copy-Item $example $envFile
        Write-Host "Criado deploy/syson/.env a partir de .env.example"
    }
}

Write-Host "A puxar imagens e a subir contentores (primeira vez pode demorar)..."
docker compose up -d --pull missing

$port = 8081
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*SYSON_HOST_PORT\s*=\s*(\d+)\s*$') { $port = [int]$Matches[1] }
    }
}

Write-Host ""
Write-Host "SysON a arrancar. Abra: http://localhost:$port"
Write-Host "Estado:  docker compose -f deploy/syson/docker-compose.yml ps"
Write-Host "Parar:   .\deploy\syson\down.ps1"
Write-Host ""
Write-Host "A aguardar HTTP (ate ~2 min na 1a vez)..."

$ok = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$port" -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) {
            $ok = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

if ($ok) {
    Write-Host "OK - SysON responde em http://localhost:$port"
} else {
    Write-Host "Contentores no ar, mas HTTP ainda nao respondeu. Veja logs:"
    Write-Host "  docker compose -f deploy/syson/docker-compose.yml logs -f app"
}
