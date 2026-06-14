param(
    [string]$Message = "Update AI stock GUI"
)

Set-Location -Path $PSScriptRoot

$files = @(
    ".gitignore",
    "AI-stock.py",
    "ai_stock_gui.py",
    "README_finmind_gui.md",
    "VERSION",
    "requirements.txt",
    "run_ai_stock.bat",
    "run_ai_stock.ps1",
    "watchlist.json",
    "sync_to_github.ps1"
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
