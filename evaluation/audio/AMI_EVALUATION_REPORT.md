# AMI Whisper evaluation record

## Purpose

This evaluation measures the accuracy and processing performance of the offline Whisper speech-to-text stage.

It does not directly measure the later personal-data detector and does not measure GDPR compliance.

## Five-clip pilot

The initial pilot used five deterministic English clips from the official AMI `ihm` test split.

`ihm` refers to individual headset microphone recordings.

The processed distribution was `edinburghcstr/ami` under CC BY 4.0.

The target Windows evaluation used:

- Python 3.11.9;
- Whisper package `20250625`;
- Whisper `tiny.en`;
- CPU execution;
- FFmpeg 8.1.2;
- application version 0.5.0 at the time of the experiment.

All 53 automated tests in that project version passed before the evaluation was run.

## Five-clip result

| Measure | Result |
|---|---:|
| Cases | 5 |
| Reference words | 90 |
| Hypothesis words | 85 |
| Substitutions | 12 |
| Deletions | 7 |
| Insertions | 2 |
| Word error rate | 0.2333 |

Per-case WER values were:

```text
0.2000
0.1053
0.2000
0.2273
0.4211
```

The strongest clip produced WER `0.1053` and the weakest produced WER `0.4211`, showing substantial variation even within the small close-microphone sample.

## Metric

Word error rate was calculated as:

```text
WER = (substitutions + deletions + insertions) / reference words
```

Before comparison:

- English text was case-folded;
- punctuation was ignored;
- apostrophes were removed.

WER is an edit-rate metric. A WER of `0.2333` therefore means that 21 word-level edit operations were required across 90 reference words.

It should not be described as `76.67% accuracy`, and WER can exceed `1.0` when insertion errors are sufficiently numerous.

## Pilot interpretation

The pilot demonstrated that the complete local audio-transcription path worked on the Windows target environment and could be measured against human reference transcripts.

The result remains limited because:

- only five clips were used;
- all clips came from one AMI meeting;
- recordings used close individual headset microphones;
- only four speakers were represented;
- noisy-room and far-field conditions were not tested;
- personal-data terminology was not specifically targeted.

## Reproducibility evidence

Recorded hashes:

- metrics SHA-256: `00d76bf60d48b0d0b8c598e222090d55d95424b334c05ae08e5ba3237eee49`
- provenance SHA-256: `60e8c6a5bc68490923c3bbd8c0036f408bc302416e8ed8bc8f5eeb7d9a39034c`

Target-machine evidence included:

```text
ami_ihm_5_metrics.json
ami_windows_evidence.txt
ami_provenance.json
```

Private reference transcripts and WAV files were excluded from the public repository.

## `tiny.en` and `base.en` comparison

A second controlled experiment compared Whisper `tiny.en` and `base.en`.

Three approximately one-minute same-speaker AMI composites were used. Together they contained:

- 181.15 seconds of speech;
- 517 reference words.

Each composite joined source-ordered utterance segments from the same meeting, speaker and headset. They were therefore longer inputs than the initial clips but were not uninterrupted one-minute extracts from the original meeting.

Both models were evaluated on the same three inputs and the same Windows target machine.

## Comparison result

| Model | Hypothesis words | S | D | I | WER | Processing time | Real-time factor |
|---|---:|---:|---:|---:|---:|---:|---:|
| `tiny.en` | 455 | 52 | 68 | 6 | **0.2437** | **8.56 s** | **0.0472** |
| `base.en` | 430 | 49 | 89 | 2 | 0.2708 | 12.36 s | 0.0682 |

`tiny.en` required 126 word-edit operations compared with 140 for `base.en`.

It produced lower overall WER and completed the evaluation approximately 31% faster.

`base.en` produced slightly fewer substitutions and insertions but substantially more deletions. It performed better on the first composite, while `tiny.en` performed better on the other two.

## Model-selection decision

`tiny.en` was retained as the final application speech model.

On this fixed CPU evaluation it provided:

- lower WER;
- shorter processing time;
- lower computational cost for the intended prototype environment.

This is an evidence-based selection for this project rather than a claim that `tiny.en` is universally more accurate than `base.en`.

Both the initial pilot and the longer comparison used close individual-headset speech from AMI meeting `EN2002a`. The result should therefore not be generalised to noisy, distant, accented or otherwise different speech conditions.

## Conclusion

Audio implementation, Windows integration, real-data WER evaluation and model selection were completed successfully.

The evaluation demonstrates a functioning offline audio stage with measurable transcription performance while also showing that transcription errors remain a significant limitation for downstream analysis.
