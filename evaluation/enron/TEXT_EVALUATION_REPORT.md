# Enron text-detection evaluation record

## Summary

A deterministic pilot of 10 Enron email messages was used to evaluate the supported text-detection categories on natural business email.

The reference set contained 115 model-assisted, human-corrected finding occurrences.

The scanner produced:

| Measure | Result |
|---|---:|
| True positives | 102 |
| False positives | 17 |
| False negatives | 13 |
| Micro precision | 0.8571 |
| Micro recall | 0.8870 |
| Micro F1 | 0.8718 |

This was a small project evaluation. It does not establish general personal-data detection accuracy and must not be interpreted as evidence of GDPR compliance.

## Method

- Source: locally downloaded Enron Email Dataset.
- Sample size: 10 messages.
- Selection: deterministic SHA-256 ranking of relative source paths using seed `3070`.
- Supported categories only:
  - `PERSON_NAME`
  - `LOCATION_REFERENCE`
  - `EMAIL_ADDRESS`
  - `PHONE_NUMBER`
  - `IP_ADDRESS`
  - `IBAN`
  - `PAYMENT_CARD_NUMBER`
- Reference data: 115 supported finding occurrences reviewed locally by one student.
- Annotation method: model-assisted human correction.
- Scanner suggestions could be accepted or rejected.
- Missed supported values were added manually.
- Matching: exact finding type and normalised value.
- Matching was occurrence-aware, so repeated occurrences were counted separately.
- Metrics: per-type and micro precision, recall and F1.
- Raw messages and private labels remained outside the public repository.

## Results

| Finding type | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Email address | 60 | 0 | 5 | 1.0000 | 0.9231 | 0.9600 |
| Location reference | 1 | 5 | 0 | 0.1667 | 1.0000 | 0.2857 |
| Person name | 39 | 12 | 8 | 0.7647 | 0.8298 | 0.7959 |
| Phone number | 2 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| **Micro overall** | **102** | **17** | **13** | **0.8571** | **0.8870** | **0.8718** |

The 115 reference occurrences comprised:

- 65 email-address occurrences;
- 1 location-reference occurrence;
- 47 person-name occurrences;
- 2 phone-number occurrences.

The scanner emitted 119 predictions across the represented categories.

No IP-address, IBAN or payment-card observations occurred in this pilot. Their implemented behaviour is tested using synthetic unit and integration fixtures instead.

## Interpretation

Email detection was the strongest represented category. No false-positive email addresses were produced, although five labelled email occurrences were missed.

Person-name recognition was less reliable. Twelve predicted names were not present in the corrected reference labels and eight labelled name occurrences were missed.

Location performance cannot be generalised from this sample. Only one labelled location was present, while five additional location predictions were rejected by the reviewer.

Both labelled phone-number occurrences were detected, but two examples are insufficient to support a general performance claim.

The overall micro F1 of `0.8718` therefore describes this particular 10-message pilot rather than expected performance on arbitrary email collections.

## Threats to validity

1. Ten messages form a small pilot rather than a representative sample of business email.
2. The deterministic sample was not stratified by finding category.
3. Only one reviewer created the corrected reference labels.
4. Inter-annotator agreement was not measured.
5. The reviewer saw scanner suggestions during annotation. Although false positives could be rejected and missed values added, suggestion exposure may have biased what was noticed.
6. Finding categories were strongly imbalanced.
7. Three supported structured-identifier categories were not represented at all.
8. Exact value matching does not award partial credit for entity-boundary differences.

## Interpretation boundary

The result supports the conclusion that the implemented text stage identified a useful proportion of supported personal-data occurrences in this small real-email pilot.

It also demonstrates that contextual entity recognition was less reliable than deterministic email detection.

The evaluation does **not** support claims of complete personal-data discovery, legal compliance, population-level accuracy or performance on unseen domains.

## Retained evidence

Privacy-safe project evidence includes:

- the aggregate evaluation result;
- per-type metrics;
- `evaluation/results/enron_pilot_10_metrics.json`;
- source-selection and evaluation code in the repository.

The raw Enron messages and corrected private annotation file are excluded from the public repository.
