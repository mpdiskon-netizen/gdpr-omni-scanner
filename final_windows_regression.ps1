$ErrorActionPreference = "Stop"

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$Scanner = Join-Path $PSScriptRoot ".venv\Scripts\gdpr-scan.exe"
if (-not (Test-Path $Python)) {
    throw "The project .venv was not found. Run setup.ps1 first."
}

$DefaultTesseractDirectory = "C:\Program Files\Tesseract-OCR"
if (-not (Get-Command tesseract -ErrorAction SilentlyContinue) -and (Test-Path $DefaultTesseractDirectory)) {
    $env:Path = "$DefaultTesseractDirectory;$env:Path"
}

function Run-Step {
    param([string]$Name, [scriptblock]$Command)
    Write-Host ""
    Write-Host "=== $Name ==="
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE."
    }
}

Run-Step "Release version" { & $Scanner --version }
Run-Step "Python version" { & $Python --version }
Run-Step "Automated tests" { & $Python -m pytest }
Run-Step "Text scan" { & $Scanner --file (Join-Path $PSScriptRoot "sample_data\synthetic_text.txt") --show-values }
Run-Step "Image scan" { & $Scanner --file (Join-Path $PSScriptRoot "sample_data\synthetic_document.png") --show-values --show-extracted-text }
Run-Step "Audio scan" { & $Scanner --file (Join-Path $PSScriptRoot "sample_data\synthetic_speech.wav") --show-values --show-extracted-text }

$Results = Join-Path $PSScriptRoot "results"
New-Item -ItemType Directory -Force $Results | Out-Null
Run-Step "JSON and CSV export" {
    & $Scanner --file (Join-Path $PSScriptRoot "sample_data\synthetic_text.txt") `
        --json-out (Join-Path $Results "final_sample.json") `
        --csv-out (Join-Path $Results "final_sample.csv") `
        --show-values
}

Write-Host ""
Write-Host "Regression complete. See README.md for the supported inputs, limitations and evaluation records."
