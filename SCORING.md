# Exposure indicator

The scanner produces a transparent **exposure indicator**, not a probability and not a GDPR-compliance decision.

Each unique detected value adds the following points:

| Finding type | Points |
|---|---:|
| Location reference | 3 |
| Person name | 5 |
| IP address | 8 |
| Email address | 10 |
| Phone number | 10 |
| IBAN | 25 |
| Payment-card number | 25 |

Repeated copies of the same normalised value count once. Each finding type is capped at three unique values, and the total is capped at 100. The cap prevents a long document containing repeated identifiers from dominating the indicator.

| Score | Displayed band |
|---:|---|
| 0 | none detected |
| 1-24 | low |
| 25-49 | moderate |
| 50-74 | high |
| 75-100 | very high |

The weights are deliberately simple and explainable. Financial identifiers receive more points than contextual person or location references because accidental exposure of an IBAN or payment-card number is normally more immediately sensitive. These are project design choices, not legal thresholds. Automated tests cover duplicate handling, per-type caps, the 100-point cap, and every score-band boundary.

