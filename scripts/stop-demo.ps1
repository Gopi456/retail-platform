param(
    [switch]$DeleteDatabase
)

$ErrorActionPreference = 'Stop'

if ($DeleteDatabase) {
    docker compose down -v
}
else {
    docker compose down
}
Write-Host 'Demo stack stopped.' -ForegroundColor Green
if ($DeleteDatabase) {
    Write-Host 'The demo database volume was deleted.' -ForegroundColor Yellow
}
