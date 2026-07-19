# Image evaluation

`gdpr-evaluate-image` measures Tesseract OCR output against supplied reference
text using character error rate (CER). Lower CER is better.

The included `sample_image_cases.jsonl` is a one-image synthetic harness check.
It proves that the evaluator and Tesseract adapter work together, but it is not
the formal result.

The formal v0.6.0 evaluation uses 25 documents from the FUNSD test split. FUNSD
contains real noisy scanned forms and supplied word-level annotations. The
forms originated from the RVL-CDIP form collection. This avoids treating
Tesseract's own predictions as reference text and avoids manually transcribing
25 full pages.

Follow `FUNSD_WINDOWS_GUIDE.md`. Images, reference text and the private manifest
remain under `evaluation_private` and are excluded from the distributable
project archive. Only score-only metrics and provenance hashes belong in the
report evidence.

CER normalisation is frozen as:

- Unicode NFKC normalisation;
- case-folding;
- all whitespace collapsed to single spaces;
- punctuation retained.

The FUNSD annotations provide text grouped into entities. The preparation tool
orders entities by top and then left box coordinates to form a deterministic
reference sequence. Complex layouts may therefore create reading-order errors
in addition to character-recognition errors; this must be stated as a
limitation.

## Controlled end-to-end set

`corporate_synthetic` contains 20 project-created PNG images and exact labels
for 69 supported findings. These are safe fictional test assets, so they may be
included in the project archive. They supplement FUNSD; they do not replace it.

Run the Tesseract end-to-end evaluation with:

```powershell
gdpr-evaluate-image-pipeline `
  --dataset evaluation\image\corporate_synthetic\corporate_image_cases.jsonl `
  --json-out evaluation\results\corporate_images_tesseract_pipeline.json
```

Follow `CONTROLLED_CORPORATE_IMAGE_GUIDE.md` for the target-Windows evidence
run and optional EasyOCR comparison.
