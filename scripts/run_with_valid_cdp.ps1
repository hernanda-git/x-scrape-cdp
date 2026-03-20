param(
    [int]$Port = 9222,
    # Must be the same user-data-dir you will log into.
    [string]$UserDataDir = ".\data\chrome_profile",
    # Defaults to the same config used when you run `python -m x_scrape_cdp.cli run` with no --config.
    [string]$ConfigPath = ".\config\default.yaml",
    # How long to wait for the CDP endpoint to become reachable.
    [int]$CdpWaitSeconds = 30,
    # How long to wait for `validate-session` to return ok (e.g. if you need to login/2FA).
    [int]$SessionWaitSeconds = 600,
    [int]$SessionCheckIntervalSeconds = 10
)

$ErrorActionPreference = "Stop"

function Resolve-RepoPath([string]$p) {
    if ([System.IO.Path]::IsPathRooted($p)) { return $p }

    # Resolve relative paths against the repo root (one level up from `scripts`).
    # Do not require existence (e.g. Chrome user-data-dir may not exist yet).
    $repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
    $child = $p -replace '^[.][\\/]',''  # strip leading `./` or `.\`.
    return [System.IO.Path]::Combine($repoRoot, $child)
}

function Test-CdpEndpoint([string]$url) {
    try {
        # Hitting /json/version is a lightweight CDP health check.
        $resp = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 2 -UseBasicParsing
        return $resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300
    } catch {
        return $false
    }
}

$resolvedConfigPath = Resolve-RepoPath $ConfigPath
$resolvedUserDataDir = [System.IO.Path]::GetFullPath((Resolve-RepoPath $UserDataDir))

$cdpBaseUrl = "http://127.0.0.1:$Port"
$cdpVersionUrl = "$cdpBaseUrl/json/version"

$env:CDP_URL = $cdpBaseUrl

Write-Host "CDP target: $cdpBaseUrl"
Write-Host "Config: $resolvedConfigPath"
Write-Host "Chrome user-data-dir: $resolvedUserDataDir"

# 1) Ensure CDP is reachable (launch Chrome only if needed).
$cdpDeadline = (Get-Date).AddSeconds($CdpWaitSeconds)
$cdpOk = Test-CdpEndpoint $cdpVersionUrl
if (-not $cdpOk) {
    $launchScript = Join-Path $PSScriptRoot "launch_chrome.ps1"
    if (-not (Test-Path $launchScript)) {
        throw "launch_chrome.ps1 not found at $launchScript"
    }

    Write-Host "CDP not reachable yet; launching Chrome..."
    & $launchScript -Port $Port -UserDataDir $resolvedUserDataDir | Out-Null
} else {
    Write-Host "CDP already reachable; skipping Chrome launch."
}

while (-not (Test-CdpEndpoint $cdpVersionUrl)) {
    if ((Get-Date) -ge $cdpDeadline) {
        throw "Timed out waiting for CDP at $cdpVersionUrl"
    }
    Start-Sleep -Seconds 1
}

Write-Host "CDP is reachable."

# 2) Validate session until it is logged in.
$pythonLauncher = "py"
$pythonVersion = "3.14"
$pythonSelector = "-$pythonVersion"
$validateDeadline = (Get-Date).AddSeconds($SessionWaitSeconds)

while ((Get-Date) -lt $validateDeadline) {
    Write-Host "Validating session (validate-session)..."
    & $pythonLauncher $pythonSelector -m x_scrape_cdp.cli validate-session --config $resolvedConfigPath | Out-Host

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Session is valid. Starting listener..."
        break
    }

    Write-Host "Session not valid yet. If needed, login manually in the Chrome window, then wait..."
    Start-Sleep -Seconds $SessionCheckIntervalSeconds
}

if ($LASTEXITCODE -ne 0) {
    throw "Timed out waiting for logged-in session. Please login in Chrome, then re-run this script."
}

# 3) Continue (listener).
& $pythonLauncher $pythonSelector -m x_scrape_cdp.cli run --config $resolvedConfigPath

