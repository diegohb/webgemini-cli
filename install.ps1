$ErrorActionPreference = 'Stop'
$repo = "expert-vision-software/GemiTerm"
$exeDir = "$env:LOCALAPPDATA\GemiTerm"
$exePath = "$exeDir\GemiTerm.exe"

if (-not (Test-Path $exeDir)) {
    New-Item -ItemType Directory -Path $exeDir -Force | Out-Null
}

$apiUrl = "https://api.github.com/repos/$repo/releases/latest"
$assets = Invoke-RestMethod $apiUrl | Select-Object -ExpandProperty assets
$exeAsset = $assets | Where-Object { $_.name -eq 'GemiTerm.exe' }

if (-not $exeAsset) {
    Write-Error "GemiTerm.exe not found in latest release. Is the repository published yet?"
    exit 1
}

Write-Host "Downloading GemiTerm..."
Invoke-WebRequest $exeAsset.browser_download_url -OutFile $exePath

Write-Host "Installing Chromium browser for Playwright..."
& $exePath install-browser

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($userPath -notlike "*$exeDir*") {
    [Environment]::SetEnvironmentVariable('Path', "$userPath;$exeDir", 'User')
    $env:Path = "$env:Path;$exeDir"
}

Write-Host "GemiTerm installed to $exePath"
Write-Host "Run 'gemiterm auth' to authenticate"