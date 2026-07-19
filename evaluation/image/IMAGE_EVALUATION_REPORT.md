# Tesseract image evaluation record

## Frozen protocol

- Model: local Tesseract English OCR.
- Dataset: FUNSD 1.0 test split.
- Sample size: 25 real noisy scanned forms.
- Selection: deterministic seeded ranking of matched test image paths.
- Reference: supplied FUNSD entity text ordered by top then left coordinate.
- Metric: character error rate (CER).
- Normalisation: Unicode NFKC, case-folding and collapsed whitespace;
  punctuation retained.
- Timing: wall-clock OCR processing time.
- Privacy: raw forms and reference text remain in `evaluation_private`.

## Rationale for using FUNSD

The initial proposal named RVL-CDIP. Its standard distribution supplies
document-class labels but not OCR transcriptions, and its full archive is about
38.8 GB. FUNSD contains real forms selected from the RVL-CDIP form collection
and adds word-level annotations suitable for OCR evaluation. It therefore
provides stronger ground truth with a smaller, reproducible educational
evaluation workflow.

## Result

The frozen Windows run completed on 18 July 2026:

- Tesseract: English 5.5.0.20241111.
- Cases: 25.
- Reference characters: 25,862.
- Hypothesis characters: 22,374.
- Total edit distance: 10,003.
- Aggregate CER: 0.3868.
- Median per-document CER: 0.3780.
- Per-document range: 0.1211 to 0.5961.
- Total OCR time: 10.7632 seconds.
- Mean OCR time: 0.4305 seconds per document.
- Metrics SHA-256: `c632a19ded909e918c5ec54552ee24fe3c82ece9ca753e85a8217542186d69cc`.
- Provenance SHA-256: `4b1f92845e30cd5e088e6bde4c50e6fde38b5f626b4d17aa60071d8c5b5e2158`.

The result means that the OCR output required 10,003 character-level edits for
25,862 normalized reference characters. CER is an error rate, not a legal-risk
score or a direct percentage of correctly recognised personal-data findings.

## Dataset terms and attribution

FUNSD was accessed from the official EPFL-LTS5 project website on 18 July
2026. Its terms restrict use to non-commercial research and educational
purposes. They also state that the real scanned images are copyrighted, derive
from RVL-CDIP and must not be made generally available. The project therefore
keeps images and annotations in `evaluation_private`, distributes no FUNSD
content, and reports only aggregate metrics, identifiers and hashes. Raw OCR
text from the forms must not be placed in the report or public repository.

Required report citation:

Jaume, G., Ekenel, H. K. and Thiran, J.-P. (2019) 'FUNSD: A Dataset for Form
Understanding in Noisy Scanned Documents', ICDAR 2019 Workshop on Open
Services and Tools for Document Analysis, arXiv:1905.13538.

Dataset and terms pages:

- <https://guillaumejaume.github.io/FUNSD/>
- <https://guillaumejaume.github.io/FUNSD/work/>

## Controlled corporate-image extension

FUNSD remains the external real-document benchmark. Its varied historical
forms provide useful evidence that Tesseract is being tested beyond clean
project fixtures, but FUNSD does not supply personal-data labels for the
scanner's supported finding types.

Version 0.6.1 therefore adds a separate set of 20 project-created PNG images.
The set covers employee and visitor badges, handwritten-style notes, meeting
notes, a business card, HR/finance/security forms, an incident report, an IT
access sheet, courier and fax sheets, a whiteboard-style note, a sign-in sheet
and an asset handover. It contains 69 exact expected finding occurrences. All
people are fictional; emails use `example.test`, IP addresses use RFC-reserved
documentation ranges, and payment details are standard test values.

This set tests the complete image -> OCR -> finding -> score path. It is useful
because corporate personal data can appear in photographs and irregular
artefacts rather than one standard form. It is controlled synthetic evidence,
not an external real-world benchmark or a claim of population accuracy.

Build-environment Tesseract baseline:

- Cases: 20; document classes: 20; expected occurrences: 69.
- OCR CER: 0.1064 (174 edits across 1,636 reference characters).
- Finding TP=49, FP=7, FN=20.
- Finding precision=0.8750, recall=0.7101 and F1=0.7840.
- Total end-to-end processing time: 13.11 seconds.
- Both badge photographs produced empty Tesseract output; this is retained as
  a real limitation rather than removed from the test set.

Target-Windows Tesseract result:

- OCR CER: 0.1039 (170 edits across 1,636 reference characters).
- OCR time: 5.4784 seconds for 20 images.
- Finding TP=50, FP=6, FN=19.
- Finding precision=0.8929, recall=0.7246 and F1=0.8000.
- End-to-end processing time: 11.05 seconds.

This target result replaces the build-environment baseline as the formal
controlled-set Tesseract result.

## Optional OCR comparison

EasyOCR 1.7.2 is the selected comparison model. It provides a
pretrained English OCR pipeline using CRAFT text detection and CRNN text
recognition, supports CPU execution, and allows its weights to be downloaded in
advance for offline use. The project is distributed under Apache License 2.0.
The primary comparison uses exactly the same 25 FUNSD documents,
normalisation, CER calculation and target Windows machine as Tesseract. The
controlled 20-image set may also be scored end to end with the same command.
Record model version, aggregate CER and processing time.

The adapter and commands are implemented in v0.6.1. EasyOCR is deliberately an
optional installation, so the normal scanner remains small.

Target-Windows EasyOCR result:

- FUNSD: CER=0.3317 across the same 25 forms; 67.1443 seconds total.
- Controlled images: CER=0.0202 (33 edits across 1,636 reference characters);
  42.4575 seconds total.
- Controlled pipeline: TP=45, FP=16, FN=24, precision=0.7377,
  recall=0.6522 and F1=0.6923; 48.91 seconds.

EasyOCR transcribed the image text more accurately, but this did not translate
into better personal-data finding performance. Tesseract produced the stronger
downstream F1 (0.8000 versus 0.6923), processed the controlled pipeline much
faster (11.05 versus 48.91 seconds), and has the smaller required installation.
Tesseract is therefore retained as the final application OCR. EasyOCR remains
comparison evidence only.

Score-only evidence hashes:

- FUNSD EasyOCR metrics: `fb9464ac0457a4e7c4ce7794a05d63786ed5e11daf274635dde4f6d04a1aedf5`.
- Controlled Tesseract CER: `96ef37c4ffba2e222eb485ab610e5e1f28715d32ff12e7dfd1ebe0f4b77576f7`.
- Controlled Tesseract pipeline: `a6ef0754f969c81f53575e53ea2c7cfaf04f5567a66657eea5f50dfbf7d1dfd6`.
- Controlled EasyOCR CER: `a857524f6250ca786fd8e329201480a9da1a7ae7a2efd9770f8696d123da54f0`.
- Controlled EasyOCR pipeline: `69896bdc4b9181d0fe916998ff677098e96d1f15e480b6bf99412495b60f158e`.
- Controlled-set provenance: `b7add5378ed3a7a053c5f9df6c795c6b901a011aa9ff699b06f98652a25fe7e9`.

- EasyOCR repository and citation information:
  <https://github.com/JaidedAI/EasyOCR>
- Official offline model hub:
  <https://www.jaided.ai/easyocr/modelhub/>
- Apache 2.0 licence:
  <https://github.com/JaidedAI/EasyOCR/blob/master/LICENSE>

## External-dataset boundary

No second external image dataset is used. This avoids adding another access,
licensing and redistribution workflow merely to increase sample count. FUNSD
provides external real-document OCR evidence; the controlled set provides
exact downstream personal-data ground truth. Their results remain separate.

## Required limitations

- This is a 25-document pilot, not a population-level accuracy claim.
- All selected documents are forms, so performance may differ for letters,
  invoices, presentations and other layouts.
- Coordinate-based reference ordering can penalise reading-order differences
  as well as character recognition errors.
- FUNSD includes noisy historical scans and its supplied annotations may contain
  errors.
- The metric differs from the word-level baselines in the original FUNSD paper,
  so the numerical results must not be compared directly.
- CER does not measure the downstream personal-data detector directly.
- The controlled corporate set was created for this project and may be easier
  than uncontrolled phone photographs; it must not be described as real data.
- Handwritten-style results are illustrative and do not establish general
  handwriting support.
- Neither CER nor the exposure indicator determines GDPR compliance.
