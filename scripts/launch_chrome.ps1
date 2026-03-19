param(
    [int]$Port = 9222,
    [string]$UserDataDir = ".\data\chrome_profile"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $UserDataDir)) {
    New-Item -ItemType Directory -Path $UserDataDir | Out-Null
}

$chromeCandidates = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
)

$chromePath = $chromeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $chromePath) {
    throw "Chrome executable not found in standard install paths."
}

$args = @(
    "--remote-debugging-port=$Port",
    "--user-data-dir=$UserDataDir",
    "--no-first-run",
    "--no-default-browser-check"
)

Start-Process -FilePath $chromePath -ArgumentList $args | Out-Null
Write-Host "Chrome launched with CDP at http://127.0.0.1:$Port"
Write-Host "Check endpoint: http://127.0.0.1:$Port/json/version"
