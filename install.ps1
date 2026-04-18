$ErrorActionPreference = 'Stop'
$repo = "expert-vision-software/GemiTerm"
$exeDir = "$env:LOCALAPPDATA\GemiTerm"
$exePath = "$exeDir\GemiTerm.exe"

if (-not (Test-Path $exeDir)) {
    New-Item -ItemType Directory -Path $exeDir -Force | Out-Null
}

$apiUrl = "https://api.github.com/repos/$repo/releases/latest"
$response = Invoke-RestMethod $apiUrl -ErrorAction SilentlyContinue

if (-not $response -or -not $response.assets) {
    Write-Host "No releases found. Building from source instead..."
    Write-Host ""
    Write-Host "To install GemiTerm:"
    Write-Host "  1. Ensure you have Python 3.11+ and pip installed"
    Write-Host "  2. Run: pip install gemiterm"
    Write-Host "  3. Run: gemiterm install-browser"
    Write-Host ""
    Write-Host "Or download a release manually from:"
    Write-Host "  https://github.com/$repo/releases"
    exit 1
}

$assets = $response.assets
$exeAsset = $assets | Where-Object { $_.name -eq 'GemiTerm.exe' }

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