# GDPR Omni-Scanner

CM3070 student project: a local English-language tool that highlights possible personal-data exposure for human review.

It does **not** determine GDPR compliance and does not provide legal advice.

## Current build: v0.7.0

Version 0.7.0 is the final assessed CLI build. Text, audio and image evaluation are complete. This release freezes the application features, validates export and failure paths, tests the exposure-score boundaries, and supplies a repeatable Windows regression script.

Implemented:

- direct text and UTF-8 `.txt` input;
- PNG/JPG printed English document-image input;
- WAV/MP3 English speech input;
- Tesseract English OCR feeding the same detection and scoring pipeline;
- Whisper `tiny.en` CPU transcription feeding the same pipeline;
- spaCy `en_core_web_sm` name/location recognition;
- deterministic email, phone, IP address, IBAN and payment-card detection;
- an explainable 0-100 exposure indicator;
- terminal output plus JSON and CSV export;
- unit and integration tests.
- a reproducible labelled-text precision/recall/F1 evaluation command.
- a deterministic local tool for selecting a traceable Enron pilot subset.
- Windows extended-path handling for the corpus's trailing-period filenames.
- a local machine-assisted annotation command with validation and automatic backup.
- a word-error-rate evaluator for Whisper reference transcripts;
- optional `tiny.en`/`base.en` evaluation comparison with elapsed processing time.
- a character-error-rate evaluator for Tesseract OCR;
- deterministic preparation of 20-30 FUNSD test documents with provenance hashes.
- a supplied 20-image controlled corporate set with 69 exact fictional labels;
- end-to-end image OCR plus finding precision/recall/F1 evaluation;
- an optional EasyOCR 1.7.2 comparison adapter.
- validated JSON/CSV export paths and readable missing/unsupported/corrupt-file errors;
- automated tests for every exposure-score band boundary;
- final Windows regression, offline-runtime and distribution-integrity instructions.

The three pretrained models are integrated: spaCy for text entities, Tesseract for document-image OCR and Whisper for speech transcription. Tesseract and Whisper convert their inputs to text, then spaCy and deterministic detectors analyse that text.

## Start here

Follow [SETUP_WINDOWS.md](SETUP_WINDOWS.md) exactly. The short version after setup is:

```powershell
gdpr-scan --file sample_data\synthetic_text.txt
```

Scan the supplied synthetic document image:

```powershell
gdpr-scan --file sample_data\synthetic_document.png --show-values --show-extracted-text
```

Scan the supplied synthetic speech sample:

```powershell
gdpr-scan --file sample_data\synthetic_speech.wav --show-values --show-extracted-text
```

Export a scan:

```powershell
gdpr-scan --file sample_data\synthetic_text.txt `
  --json-out results\sample.json `
  --csv-out results\sample.csv `
  --show-values
```

Run the tests:

```powershell
python -m pytest
```

Validate the text evaluation harness:

```powershell
gdpr-evaluate-text --dataset evaluation\sample_text_cases.jsonl `
  --json-out evaluation\results\sample_text_metrics.json
```

The included four-case dataset validates the harness only. It is deliberately too small to support a formal result and is separate from the completed Enron pilot below.

The completed 10-message Enron pilot contains 115 model-assisted, human-corrected reference occurrences. It produced micro precision `0.8571`, recall `0.8870` and F1 `0.8718`. See `evaluation\enron\TEXT_EVALUATION_REPORT.md` for the full method, per-type results and limitations. This small result is not a compliance or general-accuracy claim.

Validate the audio evaluation harness with the supplied synthetic WAV file:

```powershell
gdpr-evaluate-audio --dataset evaluation\audio\sample_audio_cases.jsonl `
  --json-out evaluation\results\sample_audio_metrics.json
```

The included audio manifest validates WER calculation and Whisper integration only. The completed five-clip AMI pilot produced WER `0.2333` on 90 reference words. Follow `evaluation\audio\AMI_V051_WINDOWS_GUIDE.md` for the final three-input model comparison.

The final comparison is complete. On the same 181.15 seconds of AMI speech, `tiny.en` produced WER `0.2437` in 8.56 seconds and `base.en` produced WER `0.2708` in 12.36 seconds. `tiny.en` is retained as the final CPU model because it was both more accurate and faster on this controlled sample.

Validate the image evaluation harness:

```powershell
gdpr-evaluate-image --dataset evaluation\image\sample_image_cases.jsonl `
  --json-out evaluation\results\sample_image_metrics.json
```

The formal image evaluation uses 25 real noisy scanned forms from the FUNSD
test split. Follow `evaluation\image\FUNSD_WINDOWS_GUIDE.md`. FUNSD adds
reference text annotations to forms selected from RVL-CDIP, allowing CER to be
calculated without manually transcribing every page.

FUNSD evaluation is complete at CER `0.3868`. Version 0.6.1 added a separate
20-image controlled set covering badges, handwritten-style notes, photographed
paper and corporate forms. Its build-environment Tesseract baseline produced
CER `0.1064` and downstream finding F1 `0.7840`. Follow
`evaluation\image\IMAGE_EVALUATION_REPORT.md` for the completed target-Windows
Tesseract/EasyOCR comparison and its limitations. The preparation guides are
retained as reproducibility evidence, not as unfinished instructions.

After separately downloading and extracting the official Enron corpus, prepare the private pilot file:

```powershell
gdpr-prepare-enron --corpus C:\datasets\enron\maildir `
  --out evaluation_private\enron_pilot_unlabelled.jsonl --limit 20
```

Follow `evaluation\enron\ANNOTATION_GUIDE.md`. The evaluator refuses unlabelled cases, and `evaluation_private` is excluded from the project archive.

Review a single case using suggestions from the local scanner:

```powershell
gdpr-annotate-enron --dataset evaluation_private\enron_pilot_unlabelled.jsonl --case 2 --assisted
```

Accept correct suggestions by type, reject false positives, and add any values the scanner missed. This last check is required for recall. The command displays private email text in the local terminal; do not screenshot or share that terminal while the text is visible.

## Privacy behaviour

- Scan content is processed locally after installation and the one-time model downloads.
- The application does not upload scan content. Whisper may download `tiny.en` if its local cache is missing.
- Results are not saved unless an export option is supplied.
- Finding values are masked in terminal output unless `--show-values` is used.
- Use only synthetic or properly authorised personal-data examples.

## Final verification and supporting records

- Run `powershell -ExecutionPolicy Bypass -File .\final_windows_regression.ps1` for the successful target-machine regression sequence. The automated tests and supplied synthetic inputs remain the authoritative reproducible checks.
- See [SCORING.md](SCORING.md) for the complete exposure-indicator calculation and tested boundaries.
- See [LICENSES_AND_ATTRIBUTION.md](LICENSES_AND_ATTRIBUTION.md) for primary software/model licences and dataset handling requirements.

## Current limitations

- English only.
- One text input at a time.
- Possible false positives and false negatives.
- The score is a transparent prioritisation heuristic, not a probability or legal assessment.
- Audio is CPU-only and intended for short, clear English recordings; the first run loads the model and may be slower.
- OCR is intended primarily for printed English; the controlled handwritten-style cases are limitation tests, not general handwriting support.
- The completed Enron, AMI and FUNSD results and the controlled image set are pilots and must not be generalised.
