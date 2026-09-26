# Exposure indicator

The scanner produces a transparent personal-data **exposure indicator**.

It is not a probability, legal assessment or GDPR-compliance decision.

## Finding weights

Each unique detected value contributes the following number of points:

| Finding type | Points |
|---|---:|
| Location reference | 3 |
| Person name | 5 |
| IP address | 8 |
| Email address | 10 |
| Phone number | 10 |
| IBAN | 25 |
| Payment-card number | 25 |

Financial identifiers receive higher weights than contextual person or location references because accidental exposure of an IBAN or payment-card number was treated as a higher-priority review case in the project design.

These weights are project design choices rather than legal thresholds.

## Duplicate handling

Findings are grouped by finding type and normalised value.

Repeated occurrences of the same normalised value contribute to the score only once.

For example, five occurrences of the same email address count as one unique email value for scoring purposes.

## Per-type cap

Each finding type contributes points for a maximum of three unique values.

For a finding type with:

- `n` unique values;
- weight `w`;

the contribution is:

```text
min(n, 3) × w
```

This prevents a long document containing many values of one category from dominating the complete indicator.

## Overall score

The contributions from all detected finding types are added together.

The final score is capped at:

```text
100
```

Therefore:

```text
score = min(100, sum of capped finding-type contributions)
```

## Display bands

| Score | Displayed band |
|---:|---|
| 0 | none detected |
| 1-24 | low |
| 25-49 | moderate |
| 50-74 | high |
| 75-100 | very high |

The bands are presentation categories for the project indicator. They are not legal classifications.

## Explainability

The command-line output displays the calculation by finding type.

For example:

```text
Exposure indicator: 33/100 (moderate)

Breakdown:
- LOCATION_REFERENCE: 1 x 3 = 3
- PERSON_NAME: 1 x 5 = 5
- IBAN: 1 x 25 = 25
```

This allows the user to see why a particular score was produced rather than receiving an unexplained prediction.

## Testing

Automated tests cover:

- duplicate normalised values;
- multiple unique values;
- the three-value per-type cap;
- the overall 100-point cap;
- zero findings;
- every displayed band boundary.

The implementation is in:

```text
src/gdpr_scanner/scoring.py
```

The exposure indicator is designed to prioritise files for human review. It must not be interpreted as evidence that a file is compliant or non-compliant with GDPR.
