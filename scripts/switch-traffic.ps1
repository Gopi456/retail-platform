param(
    [Parameter(Mandatory=$true)]
    [string]$Target,

    [Parameter(Mandatory=$true)]
    [string]$ConfigPath
)

$config = $ConfigPath.Trim("'`"")

$content = (Get-Content $config) -join [Environment]::NewLine

$content = $content -replace 'server orders-(blue|green):8081;', "server $Target`:8081;"

Set-Content -Path $config -Value $content

Write-Host "Nginx traffic target changed to $Target"