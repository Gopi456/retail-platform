param(
    [string]$Version = '4.2.1',
    [ValidateSet('DEV', 'UAT', 'PRODUCTION')]
    [string]$Environment = 'DEV',
    [int]$Port = 18081,
    [switch]$ResetDatabase
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker is not installed or is not available on PATH.'
}

$password = Read-Host 'Enter a local demo database password' -AsSecureString
$passwordText = [Runtime.InteropServices.Marshal]::PtrToStringBSTR(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
)

try {
    $env:DB_PASSWORD = $passwordText
    $env:APP_VERSION = $Version
    $env:APP_ENVIRONMENT = $Environment
    $env:APP_PORT = $Port.ToString()

    if ($ResetDatabase) {
        docker compose down -v
    }

    docker build --tag "retail-app:$Version" .
    docker compose up -d

    $healthUrl = "http://localhost:$Port/health"
    $healthy = $false
    for ($attempt = 1; $attempt -le 30; $attempt++) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing $healthUrl
            if ($response.StatusCode -eq 200) {
                $healthy = $true
                break
            }
        }
        catch {
            Start-Sleep -Seconds 2
        }
    }

    if (-not $healthy) {
        docker compose logs
        throw "Application did not become healthy: $healthUrl"
    }

    Write-Host ''
    Write-Host 'Demo stack is running.' -ForegroundColor Green
    Write-Host "Health:          $healthUrl"
    Write-Host "Database health: http://localhost:$Port/db-health"
    Write-Host "Search:          http://localhost:$Port/customers/search?q=Gopi"
    Write-Host ''
    docker compose ps
}
finally {
    $env:DB_PASSWORD = $null
}
