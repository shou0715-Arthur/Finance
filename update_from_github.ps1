$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "找不到 Git。請先安裝 Git for Windows。"
}

if (-not (Test-Path ".\.git")) {
    throw "目前資料夾不是 Git repository。請先使用 git clone 下載專案。"
}

& git pull --ff-only
if ($LASTEXITCODE -ne 0) {
    throw "GitHub 同步失敗。請先處理本機未提交變更或合併衝突。"
}

& "$PSScriptRoot\setup_windows.ps1"
exit $LASTEXITCODE
