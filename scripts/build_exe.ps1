$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -Path $ProjectRoot

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name "AIStockAnalysis" `
    --add-data "config\VERSION;config" `
    --hidden-import "matplotlib.backends.backend_tkagg" `
    --hidden-import "google.genai" `
    --hidden-import "sklearn.ensemble._forest" `
    --hidden-import "sklearn.linear_model._logistic" `
    --hidden-import "sklearn.metrics._classification" `
    --hidden-import "sklearn.pipeline" `
    --hidden-import "sklearn.preprocessing._data" `
    --exclude-module "google.genai.tests" `
    --exclude-module "matplotlib.tests" `
    --exclude-module "numpy.tests" `
    --exclude-module "pandas.tests" `
    --exclude-module "pyarrow" `
    --exclude-module "pytest" `
    --exclude-module "scipy.tests" `
    --exclude-module "sklearn.tests" `
    --exclude-module "tensorflow" `
    --exclude-module "torch" `
    ".\AI-stock.py"

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0 -and (Test-Path ".\dist\AIStockAnalysis")) {
    Copy-Item -Path ".\docs\USER_MANUAL.md" -Destination ".\dist\AIStockAnalysis\USER_MANUAL.md" -Force
    if (-not (Test-Path ".\dist\AIStockAnalysis\config")) {
        New-Item -ItemType Directory -Path ".\dist\AIStockAnalysis\config" | Out-Null
    }
    if (Test-Path ".\config\watchlist.json") {
        Copy-Item -Path ".\config\watchlist.json" -Destination ".\dist\AIStockAnalysis\config\watchlist.json" -Force
    }
}

exit $exitCode
