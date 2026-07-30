# Restaura um dump SQL para a base SysON deste PC.
# Uso: .\deploy\syson\restore-db.ps1
#      .\deploy\syson\restore-db.ps1 -File .\backups\syson_pg_20260730_120000.sql
param(
    [string]$File = ""
)

$ErrorActionPreference = "Stop"
$Here = $PSScriptRoot
Set-Location $Here

$backupDir = Join-Path $Here "backups"
if (-not $File) {
    $latest = Get-ChildItem -Path $backupDir -Filter "syson_pg_*.sql" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if (-not $latest) {
        Write-Error "Nenhum backup em $backupDir. Passe -File ou copie um .sql para backups/."
    }
    $File = $latest.FullName
}

if (-not (Test-Path $File)) {
    Write-Error "Ficheiro não encontrado: $File"
}

$running = docker compose ps --status running --services 2>$null
if ($running -notmatch "database") {
    Write-Error "Serviço 'database' não está a correr. Execute .\deploy\syson\up.ps1 primeiro."
}

Write-Host "ATENÇÃO: isto substitui os dados da base SysON neste PC."
Write-Host "Ficheiro: $File"
$confirm = Read-Host "Escreva SIM para continuar"
if ($confirm -ne "SIM") {
    Write-Host "Cancelado."
    exit 0
}

Write-Host "A restaurar..."
Get-Content -Path $File -Raw | docker compose exec -T database psql -U username -d postgres
Write-Host "OK. Recarregue http://localhost:8081 no browser."
