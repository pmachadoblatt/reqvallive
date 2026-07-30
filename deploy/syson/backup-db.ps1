# Exporta a base Postgres do SysON para deploy/syson/backups/
# Uso: .\deploy\syson\backup-db.ps1
# Leve o .sql para casa (pen / cloud) OU use modelos .sysml no Git como fonte principal.
$ErrorActionPreference = "Stop"
$Here = $PSScriptRoot
Set-Location $Here

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outDir = Join-Path $Here "backups"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outFile = Join-Path $outDir "syson_pg_$stamp.sql"

$running = docker compose ps --status running --services 2>$null
if ($running -notmatch "database") {
    Write-Error "Serviço 'database' não está a correr. Execute .\deploy\syson\up.ps1 primeiro."
}

Write-Host "A exportar para $outFile ..."
docker compose exec -T database pg_dump -U username postgres | Set-Content -Path $outFile -Encoding utf8

if (-not (Test-Path $outFile) -or (Get-Item $outFile).Length -lt 100) {
    Write-Error "Backup parece vazio. Verifique: docker compose logs database"
}

Write-Host "OK — $(Get-Item $outFile).Length bytes"
Write-Host "Para restaurar noutro PC: copie o ficheiro para deploy/syson/backups/ e corra restore-db.ps1"
