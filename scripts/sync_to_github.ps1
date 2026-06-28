param(
    [string]$Message = "Update AI stock GUI"
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -Path $ProjectRoot

$files = @(
    ".gitignore",
    "AI-stock.py",
    "app",
    "data_sources",
    "research",
    "storage",
    "analytics",
    "ml",
    "ui",
    "docs",
    "config\VERSION",
    "config\requirements.txt",
    "config\watchlist.json",
    "scripts"
)

$missing = @()
foreach ($file in $files) {
    if (Test-Path $file) {
        git add -- $file
    } else {
        $missing += $file
    }
}

if ($missing.Count -gt 0) {
    Write-Host "Skipped missing files:" ($missing -join ", ")
}

$status = git status --short
if (-not $status) {
    Write-Host "No changes to commit."
    exit 0
}

git commit -m $Message
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$branch = git branch --show-current
git push -u origin $branch
exit $LASTEXITCODE
