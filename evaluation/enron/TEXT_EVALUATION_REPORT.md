# Enron text-detection evaluation milestone

## Report-safe result

On a deterministic pilot of 10 Enron email messages containing 115 model-assisted, human-corrected reference occurrences, the scanner produced 102 true positives, 17 false positives and 13 false negatives. Using exact finding-type and normalized-value matching with repeated occurrences counted separately, micro precision was **0.8571**, recall was **0.8870**, and F1 was **0.8718**.

This is a small prototype evaluation. It does not demonstrate general personal-data detection accuracy and must not be interpreted as evidence of GDPR compliance.

## Method

- Source: the locally downloaded Enron Email Dataset.
- Selection: deterministic SHA-256 ranking of relative source paths using seed `3070`.
- Sample: 10 messages.
- Reference data: 115 supported finding occurrences reviewed locally by one student.
- Annotation method: model-assisted human correction. Scanner suggestions were accepted or rejected and missed values were added.
- Matching: exact finding type and normalized value; occurrence-aware.
- Metrics: per-type and micro precision, recall and F1.
- Privacy: raw messages and the labelled JSONL remained in `evaluation_private` and were not included in source archives or screenshots.

## Results

| Finding type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Email address | 60 | 0 | 5 | 1.0000 | 0.9231 | 0.9600 |
| Location reference | 1 | 5 | 0 | 0.1667 | 1.0000 | 0.2857 |
| Person name | 39 | 12 | 8 | 0.7647 | 0.8298 | 0.7959 |
| Phone number | 2 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| **Micro overall** | **102** | **17** | **13** | **0.8571** | **0.8870** | **0.8718** |

The 115 reference occurrences comprise 65 email addresses, 1 location reference, 47 person-name occurrences and 2 phone numbers. The scanner emitted 119 predictions across these represented types.

## Interpretation

- Email detection was the strongest represented category: no false email addresses were produced, although five labelled occurrences were missed.
- Person-name recognition was useful but imperfect. Twelve predictions were not present in the corrected reference labels and eight labelled names were missed.
- Location precision was weak because five of six location predictions were not accepted. Only one genuine location occurrence was present, so the result is unstable and should not be generalised.
- Both phone occurrences were detected, but two examples are far too few to claim general 100% performance.
- IP addresses, IBANs and payment-card numbers had no represented observations in this pilot. Their implemented behaviour is supported by synthetic unit/integration fixtures rather than this Enron result.

## Threats to validity

1. Ten messages are a small pilot rather than a representative sample of all business email.
2. The messages were selected reproducibly but were not stratified by finding type.
3. A single reviewer created the reference labels, so inter-annotator agreement was not measured.
4. The reviewer saw scanner suggestions. Although incorrect suggestions could be rejected and missed values added, suggestion exposure may have biased what was noticed and may inflate recall.
5. The type distribution was highly imbalanced, especially for locations and phone numbers.
6. Exact value matching does not give partial credit for boundary differences.

## Appropriate report claim

The result supports the claim that the implemented text stage can identify a useful proportion of supported personal-data occurrences in a small real-email pilot, with particularly strong deterministic email detection and weaker contextual entity recognition. It does not support a claim of complete personal-data discovery, legal compliance or performance on unseen domains.

## Evidence retained

- Privacy-safe Windows terminal screenshot showing 10 labelled cases and 115 labels.
- Privacy-safe Windows evaluator screenshot showing per-type and micro metrics.
- `evaluation/results/enron_pilot_10_metrics.json` containing scores only.
- Private labelled JSONL retained locally and excluded from distribution.
