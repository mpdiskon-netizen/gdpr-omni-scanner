# Controlled corporate-image evaluation — Windows guide

This extension uses 20 supplied PNG images representing varied fictional
corporate artefacts. It requires no external dataset download and contains no
real personal data.

## 1. Activate the existing project

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m pytest
```

## 2. Run the Tesseract baseline

```powershell
gdpr-evaluate-image `
  --dataset "evaluation\image\corporate_synthetic\corporate_image_cases.jsonl" `
  --json-out "evaluation\results\corporate_images_tesseract_cer.json"

gdpr-evaluate-image-pipeline `
  --dataset "evaluation\image\corporate_synthetic\corporate_image_cases.jsonl" `
  --json-out "evaluation\results\corporate_images_tesseract_pipeline.json"
```

The first command isolates OCR CER. The second also compares the final
personal-data findings with the 69 exact labels.

## 3. Install the optional comparison model

```powershell
.\setup_easyocr.ps1
```

The normal application does not require EasyOCR. This separate setup keeps the
comparison dependency out of the core installation.

## 4. Compare EasyOCR on the same 25 FUNSD forms

The private FUNSD folder is intentionally not in this ZIP. Copy
`evaluation_private\funsd` from v0.6.0 into the v0.6.1 project, or repeat the
preparation steps in `FUNSD_WINDOWS_GUIDE.md`. Then run:

```powershell
gdpr-evaluate-image `
  --dataset "evaluation_private\funsd\funsd_test_cases.jsonl" `
  --engine easyocr `
  --allow-model-download `
  --json-out "evaluation\results\funsd_test_25_easyocr_metrics.json"
```

This is the fair model comparison because both engines use the identical real
FUNSD cases and CER protocol. The first EasyOCR command downloads its weights.

## 5. Run EasyOCR on the controlled set

```powershell
gdpr-evaluate-image `
  --dataset "evaluation\image\corporate_synthetic\corporate_image_cases.jsonl" `
  --engine easyocr `
  --json-out "evaluation\results\corporate_images_easyocr_cer.json"

gdpr-evaluate-image-pipeline `
  --dataset "evaluation\image\corporate_synthetic\corporate_image_cases.jsonl" `
  --engine easyocr `
  --json-out "evaluation\results\corporate_images_easyocr_pipeline.json"
```

Both commands must now work from the local weights downloaded in step 4.

## 6. Preserve report evidence

Capture one screenshot per engine showing the command and aggregate result.
Keep the four controlled score-only JSON files plus
`funsd_test_25_easyocr_metrics.json`. Record hashes with:

```powershell
Get-FileHash "evaluation\results\corporate_images_*_*.json" -Algorithm SHA256 |
  Select-Object Path, Hash
```

Do not describe the controlled set as real-world data or general handwriting
support. Report it beside, not combined with, the 25-document FUNSD result.
