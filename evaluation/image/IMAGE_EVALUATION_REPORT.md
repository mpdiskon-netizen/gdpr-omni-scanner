# Image evaluation record

## Purpose

The image evaluation measures the performance of the document-image processing stage.

Two complementary evaluations are used:

1. OCR character error rate on real noisy FUNSD forms.
2. OCR and downstream personal-data finding performance on a controlled synthetic corporate-document set.

Neither evaluation measures GDPR compliance.

## FUNSD protocol

- OCR engine: local Tesseract English OCR.
- Dataset: FUNSD 1.0 test split.
- Sample size: 25 real noisy scanned forms.
- Selection: deterministic seeded ranking of matched test image paths.
- Reference text: supplied FUNSD entity text ordered by top then left coordinate.
- Metric: character error rate (CER).
- Normalisation:
  - Unicode NFKC;
  - case-folding;
  - collapsed whitespace;
  - punctuation retained.
- Timing: wall-clock OCR processing time.
- Privacy: raw forms and reference text remained outside the public repository.

## Why FUNSD was used

The initial project proposal identified RVL-CDIP as a possible image dataset.

The standard RVL-CDIP distribution provides document-class labels but not OCR reference transcriptions, and its complete archive is very large.

FUNSD contains real forms originating from the RVL-CDIP form collection and adds word-level annotations that can be used as OCR reference text.

This provided a smaller and more suitable dataset for measuring OCR error without manually transcribing every evaluated page.

## FUNSD result

The frozen Windows evaluation was completed on 18 July 2026.

Environment:

- Tesseract English `5.5.0.20241111`;
- 25 test documents.

Results:

| Measure | Result |
|---|---:|
| Cases | 25 |
| Reference characters | 25,862 |
| Hypothesis characters | 22,374 |
| Edit distance | 10,003 |
| Aggregate CER | 0.3868 |
| Median per-document CER | 0.3780 |
| Minimum per-document CER | 0.1211 |
| Maximum per-document CER | 0.5961 |
| Total OCR time | 10.7632 s |
| Mean OCR time | 0.4305 s |

Recorded hashes:

- metrics SHA-256: `c632a19ded909e918c5ec54552ee24fe3c82ece9ca753e85a8217542186d69cc`
- provenance SHA-256: `4b1f92845e30cd5e088e6bde4c50e6fde38b5f626b4d17aa60071d8c5b5e2158`

CER is calculated from character-level edit distance. The result therefore means that 10,003 character edits were required across 25,862 normalised reference characters.

CER is not a personal-data detection score and is unrelated to the application's exposure indicator.

## FUNSD licensing and privacy

FUNSD was accessed from the official EPFL-LTS5 project website on 18 July 2026.

The dataset terms restrict use of the underlying scanned forms and do not permit them to be redistributed freely.

The project therefore keeps FUNSD images, annotations and extracted raw text outside the public repository and reports only privacy-safe aggregate results and evidence hashes.

Citation:

Jaume, G., Ekenel, H. K. and Thiran, J.-P. (2019), *FUNSD: A Dataset for Form Understanding in Noisy Scanned Documents*, ICDAR 2019 Workshop on Open Services and Tools for Document Analysis, arXiv:1905.13538.

Sources:

<https://guillaumejaume.github.io/FUNSD/>

<https://guillaumejaume.github.io/FUNSD/work/>

## Controlled corporate-image evaluation

FUNSD provides useful real-document OCR evidence, but it does not provide reference labels for the personal-data categories supported by this scanner.

A separate controlled set of 20 project-created PNG images was therefore used to evaluate the complete:

```text
image -> OCR -> personal-data detection -> exposure score
```

pipeline.

The set contains 69 exact expected finding occurrences across 20 document classes, including:

- employee and visitor badges;
- handwritten-style notes;
- meeting notes;
- a business card;
- HR and finance documents;
- security forms;
- incident reports;
- IT access sheets;
- courier and fax documents;
- whiteboard-style notes;
- sign-in sheets;
- asset handover documents.

All names are fictional. Emails use the reserved `example.test` domain. IP addresses use documentation ranges. Payment details use standard test values.

The controlled set is useful for exact downstream evaluation but is not presented as representative real-world data.

## Controlled Tesseract results

An earlier build-environment baseline produced:

- OCR CER: `0.1064`;
- TP: `49`;
- FP: `7`;
- FN: `20`;
- precision: `0.8750`;
- recall: `0.7101`;
- F1: `0.7840`;
- total end-to-end time: `13.11` seconds.

The final target-Windows Tesseract run produced:

| Measure | Result |
|---|---:|
| OCR CER | 0.1039 |
| OCR edit distance | 170 |
| Reference characters | 1,636 |
| OCR time | 5.4784 s |
| True positives | 50 |
| False positives | 6 |
| False negatives | 19 |
| Precision | 0.8929 |
| Recall | 0.7246 |
| F1 | 0.8000 |
| End-to-end processing time | 11.05 s |

The target-Windows result is the formal controlled-set Tesseract result.

The two badge-photo cases produced empty Tesseract output in the earlier baseline and were retained as genuine failure cases rather than removed from the dataset.

## EasyOCR comparison

EasyOCR 1.7.2 was evaluated as an alternative pretrained OCR engine.

It provides:

- CRAFT-based text detection;
- CRNN-based recognition;
- CPU execution;
- downloadable model weights for subsequent offline use.

EasyOCR remains an optional comparison dependency and is not required by the normal application.

The comparison used the same FUNSD cases and the same controlled synthetic images.

### Target-Windows comparison

FUNSD:

| Engine | CER |
|---|---:|
| Tesseract | 0.3868 |
| EasyOCR | 0.3317 |

EasyOCR required `67.1443` seconds for the FUNSD run.

Controlled images:

| Measure | Tesseract | EasyOCR |
|---|---:|---:|
| CER | 0.1039 | 0.0202 |
| Finding precision | 0.8929 | 0.7377 |
| Finding recall | 0.7246 | 0.6522 |
| Finding F1 | 0.8000 | 0.6923 |
| End-to-end processing time | 11.05 s | 48.91 s |

EasyOCR transcribed the controlled images more accurately at character level.

However, that improvement did not translate into better downstream personal-data detection.

Tesseract produced:

- higher downstream finding precision;
- higher downstream recall;
- higher downstream F1;
- substantially shorter end-to-end processing time;
- a smaller required core installation.

Tesseract was therefore retained as the final OCR engine because the primary project objective is personal-data exposure detection rather than OCR quality in isolation.

The result is specific to these project datasets and should not be interpreted as evidence that Tesseract is universally superior to EasyOCR.

## Evidence hashes

Recorded target-machine and controlled-set hashes include:

- FUNSD EasyOCR metrics: `fb9464ac0457a4e7c4ce7794a05d63786ed5e11daf274635dde4f6d04a1aedf5`
- controlled Tesseract CER: `96ef37c4ffba2e222eb485ab610e5e1f28715d32ff12e7dfd1ebe0f4b77576f7`
- controlled Tesseract pipeline: `a6ef0754f969c81f53575e53ea2c7cfaf04f5567a66657eea5f50dfbf7d1dfd6`
- controlled EasyOCR CER: `a857524f6250ca786fd8e329201480a9da1a7ae7a2efd9770f8696d123da54f0`
- controlled EasyOCR pipeline: `69896bdc4b9181d0fe916998ff677098e96d1f15e480b6bf99412495b60f158e`
- controlled-set provenance: `b7add5378ed3a7a053c5f9df6c795c6b901a011aa9ff699b06f98652a25fe7e9`

EasyOCR project:

<https://github.com/JaidedAI/EasyOCR>

EasyOCR model hub:

<https://www.jaided.ai/easyocr/modelhub/>

Licence:

<https://github.com/JaidedAI/EasyOCR/blob/master/LICENSE>

## Evaluation boundaries

FUNSD and the controlled image set have different purposes and their results are kept separate.

FUNSD provides external real-document OCR evidence.

The controlled image set provides exact ground truth for the supported personal-data finding categories and allows the complete image-processing pipeline to be measured.

No second external image dataset was introduced solely to increase sample size.

## Limitations

- The FUNSD evaluation contains only 25 documents.
- All selected FUNSD documents are forms.
- Performance may differ for letters, invoices, presentations or other document layouts.
- Coordinate-based ordering of FUNSD reference text can introduce reading-order errors as well as OCR errors.
- FUNSD annotations may themselves contain errors.
- The CER metric is different from the word-level measures reported in the original FUNSD paper and should not be compared directly.
- CER measures transcription quality rather than downstream personal-data detection.
- The controlled corporate set was created specifically for this project.
- Controlled synthetic images may be easier than uncontrolled real photographs.
- Handwritten-style cases do not establish general handwriting recognition capability.
- OCR errors can cause both missed personal-data findings and false positives.
- Neither CER, finding F1 nor the exposure indicator determines GDPR compliance.
