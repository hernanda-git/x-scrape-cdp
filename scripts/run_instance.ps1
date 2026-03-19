param(
    [Parameter(Mandatory = $true)]
    [string]$Name
)

$ErrorActionPreference = "Stop"

$instancesPath = Join-Path $PSScriptRoot "..\config\instances.yaml"
if (-not (Test-Path $instancesPath)) {
    throw "instances.yaml not found at $instancesPath"
}

$content = Get-Content $instancesPath -Raw
$blocks = $content -split "(?m)^\s*-\s+name:"

$target = $null
foreach ($block in $blocks) {
    if ($block -match "^\s*`"$Name`"") {
        $target = $block
        break
    }
}

if (-not $target) {
    throw "Instance '$Name' not found in instances.yaml"
}

if ($target -notmatch "cdp_port:\s*(\d+)") {
    throw "Missing cdp_port for instance '$Name'"
}
$port = $matches[1]

if ($target -notmatch "config_path:\s*`"([^`"]+)`"") {
    throw "Missing config_path for instance '$Name'"
}
$configPath = $matches[1]

$env:CDP_URL = "http://127.0.0.1:$port"
$env:CONFIG_PATH = $configPath

Write-Host "Running instance '$Name' with CDP_URL=$env:CDP_URL CONFIG_PATH=$env:CONFIG_PATH"
python -m x_scrape_cdp.cli run
