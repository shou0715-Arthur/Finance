Set-Location -Path $PSScriptRoot
if (Test-Path ".\.venv\Scripts\python.exe") {
    & ".\.venv\Scripts\python.exe" ".\AI-stock.py"
} else {
    python ".\AI-stock.py"
}
