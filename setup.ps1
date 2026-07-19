$ErrorActionPreference = "Stop"

Write-Host "Checking Python 3.11..."
py -3.11 --version
if ($LASTEXITCODE -ne 0) { throw "Python 3.11 was not found." }

Write-Host "Checking Tesseract OCR..."
$TesseractCommand = Get-Command tesseract -ErrorAction SilentlyContinue
if (-not $TesseractCommand) {
    $DefaultTesseractDirectory = "C:\Program Files\Tesseract-OCR"
    $DefaultTesseract = Join-Path $DefaultTesseractDirectory "tesseract.exe"
    if (Test-Path $DefaultTesseract) {
        $env:Path = "$DefaultTesseractDirectory;$env:Path"
    } else {
        throw "Tesseract OCR was not found. Install Tesseract 5 with English data, then run setup.ps1 again."
    }
}
tesseract --version
if ($LASTEXITCODE -ne 0) { throw "Tesseract could not be executed." }
$TesseractLanguages = tesseract --list-langs 2>&1
if ($LASTEXITCODE -ne 0) { throw "Tesseract language data could not be listed." }
if ($TesseractLanguages -notcontains "eng") {
    throw "Tesseract English trained data (eng) is missing."
}

Write-Host "Checking FFmpeg..."
$FfmpegCommand = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $FfmpegCommand) {
    throw "FFmpeg was not found. Install it, restart PowerShell and run setup.ps1 again."
}
ffmpeg -version
if ($LASTEXITCODE -ne 0) {
    throw "FFmpeg could not be executed."
}

if (-not (Test-Path (Join-Path $PSScriptRoot ".venv"))) {
    Write-Host "Creating .venv..."
    py -3.11 -m venv (Join-Path $PSScriptRoot ".venv")
    if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed." }
}

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

function Assert-StepSucceeded {
    param([string]$Step)
    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE. Stop and keep the complete error output."
    }
}

Write-Host "Installing project dependencies..."
& $Python -m pip install --upgrade pip
Assert-StepSucceeded "pip upgrade"
Write-Host "Installing CPU-only PyTorch (CUDA is not required)..."
& $Python -m pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.3,<3"
Assert-StepSucceeded "CPU-only PyTorch installation"
& $Python -m pip install -e "${PSScriptRoot}[dev]"
Assert-StepSucceeded "project dependency installation"

Write-Host "Installing the local English spaCy model..."
& $Python -m spacy download en_core_web_sm
Assert-StepSucceeded "spaCy model download"

Write-Host "Verifying the spaCy model..."
& $Python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('spaCy model:', nlp.meta.get('name'), nlp.meta.get('version'))"
Assert-StepSucceeded "spaCy model verification"

Write-Host "Downloading and verifying the local Whisper tiny.en model..."
& $Python -c "import whisper; whisper.load_model('tiny.en', device='cpu'); print('Whisper model: tiny.en CPU ready; package', whisper.__version__)"
Assert-StepSucceeded "Whisper tiny.en model download and verification"

Write-Host "Running tests..."
& $Python -m pytest
Assert-StepSucceeded "automated tests"

Write-Host "Running the synthetic CLI smoke test..."
& (Join-Path $PSScriptRoot ".venv\Scripts\gdpr-scan.exe") --file (Join-Path $PSScriptRoot "sample_data\synthetic_text.txt") --show-values
Assert-StepSucceeded "CLI smoke test"

Write-Host "Running the synthetic document-image smoke test..."
& (Join-Path $PSScriptRoot ".venv\Scripts\gdpr-scan.exe") --file (Join-Path $PSScriptRoot "sample_data\synthetic_document.png") --show-values --show-extracted-text
Assert-StepSucceeded "image OCR smoke test"

Write-Host "Running the synthetic audio smoke test..."
& (Join-Path $PSScriptRoot ".venv\Scripts\gdpr-scan.exe") --file (Join-Path $PSScriptRoot "sample_data\synthetic_speech.wav") --show-values --show-extracted-text
Assert-StepSucceeded "Whisper audio smoke test"

Write-Host "Running the text evaluation-harness smoke test..."
& (Join-Path $PSScriptRoot ".venv\Scripts\gdpr-evaluate-text.exe") --dataset (Join-Path $PSScriptRoot "evaluation\sample_text_cases.jsonl")
Assert-StepSucceeded "text evaluation-harness smoke test"

Write-Host "Running the audio evaluation-harness smoke test..."
& (Join-Path $PSScriptRoot ".venv\Scripts\gdpr-evaluate-audio.exe") --dataset (Join-Path $PSScriptRoot "evaluation\audio\sample_audio_cases.jsonl")
Assert-StepSucceeded "audio evaluation-harness smoke test"

Write-Host "Running the image evaluation-harness smoke test..."
& (Join-Path $PSScriptRoot ".venv\Scripts\gdpr-evaluate-image.exe") --dataset (Join-Path $PSScriptRoot "evaluation\image\sample_image_cases.jsonl")
Assert-StepSucceeded "image evaluation-harness smoke test"

Write-Host ""
Write-Host "Setup complete. Run:"
Write-Host ".\.venv\Scripts\Activate.ps1"
Write-Host "gdpr-scan --file sample_data\synthetic_text.txt --show-values"
Write-Host "gdpr-scan --file sample_data\synthetic_document.png --show-values --show-extracted-text"
Write-Host "gdpr-scan --file sample_data\synthetic_speech.wav --show-values --show-extracted-text"
Write-Host "gdpr-evaluate-text --dataset evaluation\sample_text_cases.jsonl"
Write-Host "gdpr-evaluate-audio --dataset evaluation\audio\sample_audio_cases.jsonl"
Write-Host "gdpr-evaluate-image --dataset evaluation\image\sample_image_cases.jsonl"
