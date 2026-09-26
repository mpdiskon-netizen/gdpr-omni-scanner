# GDPR Omni-Scanner

CM3070 final project: an offline-first English-language tool that highlights possible personal-data exposure for human review across text, document images and audio.

The application produces an explainable exposure indicator. It does **not** determine GDPR compliance and does not provide legal advice.

## Current release

Version `0.7.0` is the frozen final project build.

Supported inputs:

| Input | Processing |
|---|---|
| Direct text | Analysed directly |
| UTF-8 `.txt` | Local text analysis |
| `.png`, `.jpg`, `.jpeg` | Tesseract OCR followed by text analysis |
| `.wav`, `.mp3` | Whisper `tiny.en` transcription followed by text analysis |

The application uses:

- spaCy `en_core_web_sm` for person and location recognition;
- deterministic detectors for email addresses, phone numbers, IP addresses, IBANs and payment-card numbers;
- Tesseract for local English OCR;
- Whisper `tiny.en` for local English speech transcription;
- an explainable 0-100 personal-data exposure indicator;
- optional JSON and CSV export;
- automated unit and integration tests.

## Architecture

All supported input types converge on a common text-analysis pipeline.

```text
Text ------------------------\
                              \
Image -> Tesseract OCR --------> text -> detectors -> exposure indicator -> output/export
                              /
Audio -> Whisper transcription/
```

Named entities are detected using spaCy. Structured identifiers are detected using deterministic rules and validation where appropriate, including MOD-97 validation for IBANs and the Luhn algorithm for payment-card candidates.

Tesseract and Whisper are used only to convert image and audio inputs into text. The same downstream detection and scoring implementation is then reused for all three modalities.

## Setup

See [SETUP_WINDOWS.md](SETUP_WINDOWS.md) for the complete Windows installation procedure.

After setup, activate the project environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Check the installed application version:

```powershell
gdpr-scan --version
```

## Example scans

### Text

```powershell
gdpr-scan --file sample_data\synthetic_text.txt
```

Finding values are masked by default.

To display the supplied synthetic values:

```powershell
gdpr-scan --file sample_data\synthetic_text.txt --show-values
```

### Document image

```powershell
gdpr-scan --file sample_data\synthetic_document.png `
  --show-values `
  --show-extracted-text
```

The image is processed with local Tesseract OCR before the extracted text enters the normal detection pipeline.

### Audio

```powershell
gdpr-scan --file sample_data\synthetic_speech.wav `
  --show-values `
  --show-extracted-text
```

The audio is transcribed with Whisper `tiny.en` on the CPU before the transcript enters the normal detection pipeline.

MP3 input is also supported:

```powershell
gdpr-scan --file sample_data\synthetic_speech.mp3 `
  --show-values `
  --show-extracted-text
```

### Direct text

```powershell
gdpr-scan --text "Alex Morgan can be reached at alex@example.test"
```

## Export

Results are not written to disk unless an export path is supplied.

```powershell
gdpr-scan --file sample_data\synthetic_text.txt `
  --json-out results\sample.json `
  --csv-out results\sample.csv `
  --show-values
```

JSON contains the full scan result, including the exposure assessment and model information. CSV contains the individual findings.

## Tests

Run the automated test suite with:

```powershell
python -m pytest
```

The tests cover detection, validation, OCR and audio integration, evaluation metrics, file routing, exports, error handling and exposure-score boundaries.

A complete target-machine regression can also be run with:

```powershell
powershell -ExecutionPolicy Bypass -File .\final_windows_regression.ps1
```

## Evaluation

The project uses separate evaluation approaches for text, audio and document images.

### Text

A deterministic 10-message Enron pilot contained 115 model-assisted, human-corrected supported finding occurrences.

The scanner produced:

- true positives: `102`;
- false positives: `17`;
- false negatives: `13`;
- micro precision: `0.8571`;
- micro recall: `0.8870`;
- micro F1: `0.8718`.

See [evaluation/enron/TEXT_EVALUATION_REPORT.md](evaluation/enron/TEXT_EVALUATION_REPORT.md).

### Audio

A five-clip AMI pilot produced a Whisper `tiny.en` word error rate of `0.2333` across 90 reference words.

A separate controlled comparison used 181.15 seconds of AMI speech:

| Model | WER | Processing time |
|---|---:|---:|
| `tiny.en` | 0.2437 | 8.56 s |
| `base.en` | 0.2708 | 12.36 s |

`tiny.en` was retained for the final application because it produced both lower WER and shorter processing time on this fixed CPU comparison.

See [evaluation/audio/AMI_EVALUATION_REPORT.md](evaluation/audio/AMI_EVALUATION_REPORT.md).

### Images

The formal external OCR evaluation used 25 FUNSD test documents.

Tesseract produced an aggregate character error rate of `0.3868`.

A separate 20-image controlled synthetic set was used to measure both OCR and downstream personal-data detection. On the target Windows environment, Tesseract produced:

- OCR CER: `0.1039`;
- finding precision: `0.8929`;
- finding recall: `0.7246`;
- finding F1: `0.8000`;
- end-to-end processing time: `11.05` seconds.

EasyOCR produced lower OCR error on the same controlled images but weaker downstream finding F1 and substantially longer processing time. Tesseract was therefore retained as the final application OCR engine.

See [evaluation/image/IMAGE_EVALUATION_REPORT.md](evaluation/image/IMAGE_EVALUATION_REPORT.md).

These are small project evaluations and must not be interpreted as population-level accuracy or evidence of legal compliance.

## Privacy behaviour

- Scan content is processed locally after software and required model files have been installed.
- The application does not upload scan content.
- Whisper may download `tiny.en` if the model is not already present in the local cache.
- Results are not persisted unless an export option is explicitly supplied.
- Finding values are masked in normal terminal output unless `--show-values` is used.
- Evaluation material containing real data is kept outside the public repository.
- Supplied demonstration files contain synthetic or fictional data.

## Exposure indicator

The exposure indicator is deliberately simple and explainable.

Different finding types contribute different fixed weights. Repeated copies of the same normalised value count once, per-type contributions are capped, and the overall score is capped at 100.

The complete calculation and score bands are documented in [SCORING.md](SCORING.md).

The indicator is a prioritisation heuristic. It is not a probability, legal assessment or GDPR-compliance decision.

## Current limitations

- English only.
- One text input at a time.
- False positives and false negatives remain possible.
- spaCy entity recognition is contextual and can misclassify names or locations.
- OCR is intended primarily for printed English documents.
- Handwritten-style controlled examples are limitation tests rather than evidence of general handwriting support.
- Audio processing is CPU-only and intended primarily for short, clear English recordings.
- Audio performance may differ substantially for noisy, distant or accented speech.
- The evaluation datasets and sample sizes are limited.
- The exposure indicator is a project-designed heuristic rather than a legal or statistical risk model.

## Additional documentation

- [SETUP_WINDOWS.md](SETUP_WINDOWS.md) — Windows installation and verification
- [SCORING.md](SCORING.md) — exposure-indicator calculation
- [LICENSES_AND_ATTRIBUTION.md](LICENSES_AND_ATTRIBUTION.md) — external software, models and datasets
- [evaluation/enron/TEXT_EVALUATION_REPORT.md](evaluation/enron/TEXT_EVALUATION_REPORT.md) — text evaluation
- [evaluation/audio/AMI_EVALUATION_REPORT.md](evaluation/audio/AMI_EVALUATION_REPORT.md) — audio evaluation
- [evaluation/image/IMAGE_EVALUATION_REPORT.md](evaluation/image/IMAGE_EVALUATION_REPORT.md) — image evaluation
