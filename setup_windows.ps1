$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

if (-not (Test-Path ".\requirements.txt")) {
    throw "找不到 requirements.txt。請在專案資料夾內執行此腳本。"
}

$venvPython = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.11 -m venv .venv
        if ($LASTEXITCODE -ne 0) {
            & py -3 -m venv .venv
        }
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv .venv
    } else {
        throw "找不到 Python。請先安裝 Python 3.11 或更新版本，並勾選 Add Python to PATH。"
    }
}

if (-not (Test-Path $venvPython)) {
    throw "建立 .venv 失敗。請確認已安裝 Python 3.11 或更新版本。"
}

& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& $venvPython -m pip install -r .\requirements.txt
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& $venvPython -m pip check
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "安裝完成。執行 .\run_ai_stock.ps1 或 .\run_ai_stock.bat 啟動程式。" -ForegroundColor Green
