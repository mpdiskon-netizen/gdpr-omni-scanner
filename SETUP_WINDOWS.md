# Windows 11 setup

This guide installs version `0.7.0` of the GDPR Omni-Scanner on Windows 11.

The application uses Python 3.11, local Tesseract OCR and CPU-based Whisper. CUDA and an NVIDIA GPU are not required.

## 1. Prerequisites

The following software is required:

- Python 3.11
- Tesseract 5 with English language data
- FFmpeg
- Git, if cloning the repository directly

## 2. Install Python 3.11

Install a 64-bit Python 3.11 release from the official Python website.

During installation, enable:

```text
Add python.exe to PATH
```

Verify the installation in a new PowerShell window:

```powershell
py -3.11 --version
```

The output should identify Python 3.11.

## 3. Install Tesseract OCR

Follow the Windows installation information in the official Tesseract documentation:

<https://tesseract-ocr.github.io/tessdoc/Installation.html#windows>

A common Windows installation location is:

```text
C:\Program Files\Tesseract-OCR
```

Verify the executable:

```powershell
& "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
```

Verify that English language data is available:

```powershell
& "C:\Program Files\Tesseract-OCR\tesseract.exe" --list-langs
```

The language list must contain:

```text
eng
```

## 4. Install FFmpeg

Using `winget`:

```powershell
winget install --id Gyan.FFmpeg --exact
```

After installation, open a new PowerShell window and verify:

```powershell
ffmpeg -version
```

FFmpeg must be available on `PATH` for Whisper audio processing.

## 5. Obtain the project

Clone the public repository:

```powershell
git clone https://github.com/mpdiskon-netizen/gdpr-omni-scanner.git
cd gdpr-omni-scanner
```

Alternatively, download the repository as a ZIP from GitHub, extract it and open PowerShell inside the extracted folder.

The project root should contain files and directories including:

```text
README.md
pyproject.toml
setup.ps1
src
tests
sample_data
evaluation
```

## 6. Recommended automatic setup

From the project root, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

The setup script:

- checks Python 3.11;
- checks Tesseract and English OCR data;
- checks FFmpeg;
- creates `.venv`;
- installs CPU-only PyTorch;
- installs the project and development dependencies;
- downloads the spaCy English model;
- downloads and verifies Whisper `tiny.en`;
- runs the automated test suite;
- runs synthetic text, image and audio smoke tests;
- runs the supplied evaluation-harness checks.

When setup completes successfully, activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 7. Manual installation

If manual setup is preferred, create and activate the virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install CPU-only PyTorch:

```powershell
python -m pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.3,<3"
```

Install the project and test dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Install the spaCy English model:

```powershell
python -m spacy download en_core_web_sm
```

Download and verify Whisper `tiny.en`:

```powershell
python -c "import whisper; whisper.load_model('tiny.en', device='cpu'); print('Whisper tiny.en CPU model OK')"
```

## 8. Verify the installation

Check the scanner version:

```powershell
gdpr-scan --version
```

Run the automated tests:

```powershell
python -m pytest
```

## 9. Run the supplied text example

```powershell
gdpr-scan --file sample_data\synthetic_text.txt
```

To display the synthetic finding values:

```powershell
gdpr-scan --file sample_data\synthetic_text.txt --show-values
```

## 10. Run the supplied document-image example

```powershell
gdpr-scan --file sample_data\synthetic_document.png `
  --show-values `
  --show-extracted-text
```

The output should identify Tesseract and spaCy, display the extracted synthetic text and show the detected findings and exposure indicator.

## 11. Run the supplied audio example

```powershell
gdpr-scan --file sample_data\synthetic_speech.wav `
  --show-values `
  --show-extracted-text
```

MP3 routing can also be verified with:

```powershell
gdpr-scan --file sample_data\synthetic_speech.mp3 `
  --show-values `
  --show-extracted-text
```

## 12. Scan direct text

```powershell
gdpr-scan --text "Alex Morgan can be reached at alex@example.test"
```

Values are masked unless `--show-values` is supplied.

## 13. Export JSON and CSV

```powershell
gdpr-scan --file sample_data\synthetic_text.txt `
  --json-out results\sample.json `
  --csv-out results\sample.csv `
  --show-values
```

The `results` directory is created automatically when required.

## 14. Evaluation-harness checks

The repository includes small synthetic fixtures for checking the evaluation implementations.

Text:

```powershell
gdpr-evaluate-text `
  --dataset evaluation\sample_text_cases.jsonl `
  --json-out evaluation\results\sample_text_metrics.json
```

Audio:

```powershell
gdpr-evaluate-audio `
  --dataset evaluation\audio\sample_audio_cases.jsonl `
  --json-out evaluation\results\sample_audio_metrics.json
```

Image:

```powershell
gdpr-evaluate-image `
  --dataset evaluation\image\sample_image_cases.jsonl `
  --json-out evaluation\results\sample_image_metrics.json
```

These fixtures validate the evaluation code. They are not substitutes for the formal Enron, AMI or FUNSD project evaluations.

## 15. Final regression

The project includes a repeatable Windows regression script:

```powershell
powershell -ExecutionPolicy Bypass -File .\final_windows_regression.ps1
```

It checks:

- application version;
- Python version;
- automated tests;
- text scanning;
- image scanning;
- audio scanning;
- JSON and CSV export.

## Offline behaviour

Internet access is required during initial installation for Python packages and model downloads.

After the required packages, spaCy model and Whisper model are available locally, scan processing does not require network access.

Tesseract runs locally. Whisper runs on the CPU. Input content is not uploaded by the application.

If the Whisper model is missing from the local cache, Whisper may attempt to download it before processing.
