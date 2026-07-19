$ErrorActionPreference = "Stop"

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Run setup.ps1 first so that the project virtual environment exists."
}

Write-Host "Installing the optional EasyOCR comparison model..."
& $Python -m pip install "easyocr==1.7.2"
if ($LASTEXITCODE -ne 0) { throw "EasyOCR installation failed." }

# Keep Torch and Torchvision on matching CPU-only builds.
Write-Host "Installing the CPU-only Torchvision build..."
& $Python -m pip install --force-reinstall --no-deps `
    --index-url "https://download.pytorch.org/whl/cpu" torchvision
if ($LASTEXITCODE -ne 0) { throw "CPU-only Torchvision installation failed." }

& $Python -c "import easyocr, torch, torchvision; print('EasyOCR', easyocr.__version__, '| Torch', torch.__version__, '| Torchvision', torchvision.__version__)"
if ($LASTEXITCODE -ne 0) { throw "EasyOCR import check failed." }

Write-Host ""
Write-Host "EasyOCR is installed. Follow evaluation\image\CONTROLLED_CORPORATE_IMAGE_GUIDE.md."
