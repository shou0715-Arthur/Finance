Set-Location -Path $PSScriptRoot

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name "AIStockAnalysis" `
    --add-data "VERSION;." `
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
    Copy-Item -Path ".\USER_MANUAL.md" -Destination ".\dist\AIStockAnalysis\USER_MANUAL.md" -Force
    if (Test-Path ".\watchlist.json") {
        Copy-Item -Path ".\watchlist.json" -Destination ".\dist\AIStockAnalysis\watchlist.json" -Force
    }
    if (Test-Path ".\industry_chain.json") {
        Copy-Item -Path ".\industry_chain.json" -Destination ".\dist\AIStockAnalysis\industry_chain.json" -Force
    }
}

exit $exitCode
