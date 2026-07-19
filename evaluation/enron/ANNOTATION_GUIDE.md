# Enron pilot annotation guide

## Scope

Annotate only the finding types the application supports:

- `PERSON_NAME`
- `LOCATION_REFERENCE`
- `EMAIL_ADDRESS`
- `PHONE_NUMBER`
- `IP_ADDRESS`
- `IBAN`
- `PAYMENT_CARD_NUMBER`

This is a small value-level evaluation, not a complete annotation of every kind of personal data.

## Procedure

1. Work only in `evaluation_private/enron_pilot_unlabelled.jsonl`.
2. Use `gdpr-annotate-enron --dataset evaluation_private\enron_pilot_unlabelled.jsonl --case 2 --assisted`, changing the case number as work progresses.
3. For each finding type, inspect the grouped scanner suggestions. Accept correct groups or review them individually; reject false positives.
4. Check the email for values the scanner did not suggest and add every missed occurrence. This step is necessary to measure false negatives and recall.

   `{"finding_type":"EMAIL_ADDRESS","value":"person@example.com"}`

5. Preserve the value exactly as it appears in `text`.
6. Repeated suggestions are grouped for convenience but stored as separate occurrences because matching is occurrence-aware.
7. Mark the case fully reviewed only after checking all seven supported types. This changes the status to `labelled` and records the assisted annotation method and model identifiers.
8. Do not place raw Enron messages or the labelled private file in screenshots, the report, Git or a downloadable project archive.

## Decisions

- Annotate a full personal name when the text provides one. Do not label an isolated generic title such as `Manager`.
- Annotate a location only when it names a geographical place or facility location supported by the scanner.
- Annotate email addresses in headers and bodies.
- Annotate phone numbers only when their context and formatting make them plausible telephone numbers.
- Annotate syntactically valid IP addresses, IBANs and payment-card numbers if present. Do not invent missing examples.
- If uncertain, record the case ID and question separately rather than guessing.

## Quality check

After the assisted pilot, manually review a small fixed audit subset without relying on suggestions. This gives a limited check for suggestion-driven bias. The evaluator refuses files that still contain `annotation_status: unlabelled`.

The report must describe this as **model-assisted, human-corrected annotation**, not independent blind ground truth. The reviewer can correct false positives and add false negatives, but suggestions may still bias what is noticed. The small blind audit and the lack of inter-annotator agreement must be acknowledged as limitations.
