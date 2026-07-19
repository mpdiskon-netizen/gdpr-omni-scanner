# Evaluation protocol and completion record — v0.6.1

The evaluation design was frozen at v0.4 Step 1 and executed through v0.6.1. Text, audio and image evaluations are now complete. The numbered plan below is retained as historical protocol evidence.

## Purpose

Evaluate the selected pretrained models and the integrated scanner. The project does not train or fine-tune a neural network unless later evidence demonstrates that this is necessary.

## Dataset roles

| Domain | Dataset | Use in this project | Ground-truth preparation |
|---|---|---|---|
| Text | Enron Email Dataset | Test supported personal-data findings in natural email text | Select a fixed, documented subset and manually label only the supported finding types. Enron does not natively provide PII labels. |
| Audio | AMI Meeting Corpus | Measure English transcription performance | Use official audio and manual transcripts to calculate word error rate (WER). |
| Image | FUNSD test split (forms selected from RVL-CDIP) | Test OCR on real noisy scanned documents | Select 25 deterministic test forms and calculate character error rate (CER) against supplied annotations. |
| Image pipeline | Controlled corporate image set v1 | Test image-to-finding behaviour across badges, notes and forms | Generate 20 fixed PNGs with 69 fictional/reserved exact labels; report CER plus finding precision, recall and F1. |

Primary dataset pages:

- Enron: <https://www.cs.cmu.edu/~enron/>
- AMI: <https://groups.inf.ed.ac.uk/ami/corpus/>
- FUNSD: <https://guillaumejaume.github.io/FUNSD/>
- FUNSD terms: <https://guillaumejaume.github.io/FUNSD/work/>
- RVL-CDIP background: <https://adamharley.com/rvl-cdip/>

Dataset files will not be committed to the project archive. Record the source, licence/terms, retrieval date, selected item identifiers and checksums in the evaluation manifest.
FUNSD is used only for this non-commercial educational evaluation. Its images,
annotations and extracted raw text must remain private and must not be included
in a public repository or submission archive.

## Frozen text metric

The first harness calculates value-level precision, recall and F1. A prediction matches when its finding type and normalized value equal the manual label. Matching is occurrence-aware. Both micro-averaged and per-type results are reported.

The included `sample_text_cases.jsonl` is only a harness-validation fixture. It is not a formal accuracy dataset and its result must not be presented as final model performance.

## Frozen execution plan (now completed)

1. Use the implemented deterministic selector and frozen guide to prepare a maximum 20-message Enron pilot subset.
2. Create model-assisted, human-corrected labels: accept or reject grouped predictions and explicitly add missed supported values.
3. A separate blind audit was planned but not completed. The final report must state this explicitly and treat suggestion bias, single-reviewer labelling and the absence of inter-annotator agreement as threats to validity. Do not imply that an independent audit occurred.
4. Add WER evaluation for a small fixed AMI subset.
5. Run CER evaluation for the fixed 25-document FUNSD subset.
6. Measure processing time on the target Windows machine.
7. Compare only a small number of justified configurations.

Optional comparison: compare Tesseract with pretrained English EasyOCR 1.7.2
on the same 25 FUNSD cases. Do not add a second external image dataset merely
to increase sample count. The controlled 20-image set is separate from FUNSD
and must be reported as synthetic project-created evidence.

## Completion status at v0.6.1

- Text steps are complete using the 10-message Enron pilot.
- Audio WER and timing are complete using the five-clip pilot and three-composite `tiny.en`/`base.en` comparison. `tiny.en` is retained.
- Image CER evaluation is complete on 25 deterministic FUNSD test documents: aggregate CER 0.3868 and mean OCR time 0.4305 seconds per document.
- Target-Windows controlled-image evaluation is complete. Tesseract produced
  CER=0.1039 and finding F1=0.8000; EasyOCR produced CER=0.0202 and finding
  F1=0.6923 on the identical 20 images.
- On the identical 25 FUNSD cases, EasyOCR produced CER=0.3317 compared with
  Tesseract CER=0.3868. Tesseract remains the application OCR because it was
  faster and produced better downstream finding F1 in the controlled pipeline.
- Remaining system checks and final usability evidence remain pending.

## Reporting boundaries

- Report measured results, including weak results and errors.
- Do not describe publicly accessible data as public domain unless its licence explicitly says so.
- Do not infer legal or GDPR compliance from precision, recall, F1, WER, CER or the exposure indicator.
- Do not include unnecessary personal data in screenshots or the final report.
