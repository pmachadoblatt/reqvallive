# Para SysON sem apagar a base (projetos ficam no volume).
# Para apagar TUDO: .\deploy\syson\down.ps1 -Wipe
param(
    [switch]$Wipe
)

$ErrorActionPreference = "Stop"
$Here = $PSScriptRoot
Set-Location $Here

if ($Wipe) {
    Write-Host "A parar e a APAGAR o volume da base (projetos SysON perdidos neste PC)..."
    docker compose down -v
} else {
    Write-Host "A parar contentores (volume mantido)..."
    docker compose down
}

Write-Host "OK."
