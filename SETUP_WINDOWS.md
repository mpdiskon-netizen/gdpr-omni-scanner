# Windows 11 setup - step by step

This guide sets up version 0.7.0 of the CLI scanner and its text, audio and image evaluation tools. It uses CPU-only Whisper; CUDA and an NVIDIA GPU are **not required**.

## If you already tested an earlier version

Keep the old version folders and screenshots as iteration evidence. Extract v0.7.0 into a new neighbouring folder. The new setup creates its own clean `.venv`.

## 1. Download and extract the project

1. Download `gdpr-omni-scanner-v0.7.0.zip`.
2. In File Explorer, right-click the ZIP and select **Extract All**.
3. Move the extracted `gdpr-omni-scanner` folder somewhere simple, for example:

   `C:\Users\YOUR_NAME\Documents\CM3070\gdpr-omni-scanner`

Do not work directly inside the ZIP.

## 2. Install Tesseract 5 for Windows

1. Follow the Windows link in the official Tesseract installation documentation: <https://tesseract-ocr.github.io/tessdoc/Installation.html#windows>.
2. Download a current 64-bit Tesseract 5 installer from the linked UB Mannheim page.
3. Install it in the default location: `C:\Program Files\Tesseract-OCR`.
4. Ensure English language data is selected. English is normally included by default.
5. Open a new PowerShell window and run:

```powershell
& "C:\Program Files\Tesseract-OCR\tesseract.exe" --version
& "C:\Program Files\Tesseract-OCR\tesseract.exe" --list-langs
```

The language list must contain `eng`.

## 3. Install FFmpeg for Whisper

In a normal PowerShell window, run:

```powershell
winget install --id Gyan.FFmpeg --exact
```

Accept the source terms if prompted. Close every PowerShell window when installation finishes, open a new one, then verify:

```powershell
ffmpeg -version
```

If `winget` is unavailable, use a Windows build linked from the official FFmpeg download page: <https://ffmpeg.org/download.html>. FFmpeg must be on `PATH` before setup continues.

## 4. Install Python 3.11

1. Open <https://www.python.org/downloads/release/python-3119/>.
2. Download **Windows installer (64-bit)** for Python 3.11.9. This version has an official Windows installer and is suitable for the project.
3. Run the installer.
4. Tick **Add python.exe to PATH**.
5. Choose **Install Now**.
6. When installation finishes, open a new PowerShell window and run:

```powershell
py -3.11 --version
```

The output must start with `Python 3.11`.

## 5. Open the project in PowerShell

In File Explorer, open the extracted project folder. Click the address bar, type `powershell`, and press Enter.

Confirm the prompt is inside the folder containing `pyproject.toml`:

```powershell
Get-ChildItem
```

You should see `pyproject.toml`, `README.md`, `src`, `tests` and `sample_data`.

## 6. Create the isolated Python environment

Run:

```powershell
py -3.11 -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Your prompt should now begin with `(.venv)`.

If PowerShell blocks activation, run this once in the same window and try again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

This changes the policy only for the current PowerShell process.

## 7. Install the project and test tools

With `(.venv)` visible, run:

```powershell
python -m pip install --upgrade pip
python -m pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.3,<3"
python -m pip install -e ".[dev]"
```

The middle command deliberately installs CPU-only PyTorch before Whisper. This prevents the environment from downloading unnecessary CUDA/NVIDIA packages.

Optional shortcut: after installing Tesseract and Python, the remaining setup can instead be run from the project folder with:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

The script checks Tesseract and FFmpeg, creates only the project `.venv`, installs CPU dependencies/models, and runs text, image, audio and evaluation smoke tests. It is the recommended route for a new v0.7.0 folder.

## 8. Download the English spaCy model

Run:

```powershell
python -m spacy download en_core_web_sm
```

This is a one-time model download.

Verify the model:

```powershell
python -c "import spacy; spacy.load('en_core_web_sm'); print('spaCy model OK')"
```

Display the installed model metadata:

```powershell
python -m spacy info en_core_web_sm
```

## 9. Download the English Whisper model

Run:

```powershell
python -c "import whisper; whisper.load_model('tiny.en', device='cpu'); print('Whisper tiny.en CPU model OK')"
```

This downloads the pretrained `tiny.en` model once and stores it in your user cache. After Python packages, spaCy, Whisper and their model files are present, scanning does not need an internet connection.

## 10. Run the automated tests

Run:

```powershell
python -m pytest
```

All 85 tests must pass. A skipped or failed spaCy, Tesseract or Whisper test means the three-model MVP is not complete. The first run may take longer while Whisper loads. Keep a screenshot of the genuine result for the report evidence log. Do not edit or invent the result.

## 11. Run the supplied synthetic text example

Run:

```powershell
gdpr-scan --file sample_data\synthetic_text.txt --show-values
```

The command should display findings and an exposure-indicator breakdown.

## 12. Run the supplied synthetic document image

Run:

```powershell
gdpr-scan --file sample_data\synthetic_document.png --show-values --show-extracted-text
```

The output should list a Tesseract English model, the spaCy model, seven findings and the explainable score. Your installed Tesseract version may differ from the development environment.

## 13. Run the supplied synthetic speech sample

Run:

```powershell
gdpr-scan --file sample_data\synthetic_speech.wav --show-values --show-extracted-text
```

The output should list `whisper:tiny.en`, CPU, the spaCy model, the transcript, person/location findings and an explainable score. This is synthetic test speech, not a real person's recording.

Also verify MP3 routing:

```powershell
gdpr-scan --file sample_data\synthetic_speech.mp3 --show-values --show-extracted-text
```

## 14. Export JSON and CSV

Run:

```powershell
gdpr-scan --file sample_data\synthetic_text.txt `
  --json-out results\sample.json `
  --csv-out results\sample.csv `
  --show-values
```

Open the new `results` folder and inspect both files. These exports contain the synthetic findings, so do not replace the sample with real personal data for screenshots.

## 15. Validate the text evaluation harness

Run:

```powershell
gdpr-evaluate-text --dataset evaluation\sample_text_cases.jsonl `
  --json-out evaluation\results\sample_text_metrics.json
```

The expected validation result currently includes seven true positives, one false-positive person name and a micro F1 of approximately `0.9333`. This is useful proof that the harness detects errors. It is not a formal accuracy result because the fixture has only four synthetic cases.

## 16. Scan directly entered text

PowerShell example:

```powershell
gdpr-scan --text "Alex Morgan can be reached at alex@example.test"
```

Values are masked unless you add `--show-values`.

## 17. Validate the image evaluation harness

Run:

```powershell
gdpr-evaluate-image --dataset evaluation\image\sample_image_cases.jsonl `
  --json-out evaluation\results\sample_image_metrics.json
```

The supplied clear synthetic document should normally produce CER `0.0000`.
This checks the evaluator only and is not the formal real-document result.

For the formal 25-document evaluation, follow:

```text
evaluation\image\FUNSD_WINDOWS_GUIDE.md
```

## 18. Open the project in VS Code

If VS Code is installed:

```powershell
code .
```

Install Microsoft's **Python** extension if VS Code recommends it. Select the interpreter inside `.venv` when prompted.

## 19. Complete the final evidence check

After setup and the normal examples work, run the successful regression steps together with:

```powershell
powershell -ExecutionPolicy Bypass -File .\final_windows_regression.ps1
```

The checklist then guides the intentional failure checks, offline-after-installation check and final archive hash separately.

## Daily workflow

Each time you return to the project:

```powershell
cd C:\Users\YOUR_NAME\Documents\CM3070\gdpr-omni-scanner
.\.venv\Scripts\Activate.ps1
python -m pytest
```

Then run the CLI or continue development.

To leave the environment:

```powershell
deactivate
```

## What to retain when asking for technical help

After setup, retain or share only:

1. the output of `py -3.11 --version`;
2. the final summary from `python -m pytest`;
3. the complete output of the synthetic WAV `gdpr-scan` command;
4. the complete `gdpr-evaluate-text` summary;
5. any complete error message if a step fails.

Do not send passwords, API keys, private files, or genuine personal data.
