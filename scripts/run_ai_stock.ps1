$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -Path $ProjectRoot
if (Test-Path ".\.venv\Scripts\python.exe") {
    & ".\.venv\Scripts\python.exe" ".\AI-stock.py"
} else {
    python ".\AI-stock.py"
}
