# AMI Whisper evaluation record

## Purpose

This evaluation measures the accuracy of the offline Whisper speech-to-text stage. It does not measure GDPR compliance and it does not directly measure the later personal-data detector.

## Completed five-clip pilot

The pilot used five deterministic English clips from the official AMI `ihm` test split. `ihm` means individual headset microphone. The processed distribution was `edinburghcstr/ami` under CC BY 4.0.

The target Windows run used Python 3.11.9, Whisper package 20250625 with `tiny.en` on CPU, FFmpeg 8.1.2 and application v0.5.0. All 53 automated tests passed before evaluation.

| Measure | Result |
|---|---:|
| Cases | 5 |
| Reference words | 90 |
| Hypothesis words | 85 |
| Substitutions | 12 |
| Deletions | 7 |
| Insertions | 2 |
| Word error rate | 0.2333 (23.33%) |

Per-case WER was 0.2000, 0.1053, 0.2000, 0.2273 and 0.4211. The best case was 10.53% and the weakest was 42.11%, showing that performance varied even within this small close-microphone sample.

The score was calculated as:

`WER = (substitutions + deletions + insertions) / reference words`

English text was case-folded, punctuation was ignored and apostrophes were removed before matching.

## Interpretation

The pilot confirms that the complete offline audio path works on Windows and gives a measurable result against human reference transcripts. A WER of 23.33% means that 21 word-level edit operations were needed across 90 reference words. It must not be described as 76.67% accuracy because WER is an edit-rate metric and can exceed 100% when insertions are numerous.

The result is only a small pilot. All clips came from one AMI meeting, used close individual headset microphones and represented four speakers. It is not evidence of performance on noisy rooms, different accents, long recordings or personal-data terms specifically.

## Reproducibility evidence

- Metrics SHA-256: `00d76bf60d48b0d0b8c598e222090d55d95424b334c05ae08e5ba3237eee49`
- Provenance SHA-256: `60e8c6a5bc68490923c3bbd8c0036f408bc302416e8ed8bc8f5eeb7d9a39034c`
- Target-machine artifacts: `ami_ihm_5_metrics.json`, `ami_windows_evidence.txt`, and private `ami_provenance.json`

The numeric values above were checked against the target-machine console output. The score-only JSON and evidence text should be copied into the final project evidence folder; the private reference transcripts and WAV files must remain excluded from public archives.

## Completed v0.5.1 model comparison

The final extension used three approximately one-minute, same-speaker AMI composites containing 181.15 seconds of speech and 517 reference words. The same inputs were evaluated with `tiny.en` and `base.en` on the Windows target machine.

| Model | Hypothesis words | S | D | I | WER | Processing time | Real-time factor |
|---|---:|---:|---:|---:|---:|---:|---:|
| `tiny.en` | 455 | 52 | 68 | 6 | **0.2437** | **8.56 s** | **0.0472** |
| `base.en` | 430 | 49 | 89 | 2 | 0.2708 | 12.36 s | 0.0682 |

`tiny.en` required 126 word-edit operations compared with 140 for `base.en`. It had lower WER and completed the evaluation approximately 31% faster. `base.en` made slightly fewer substitutions and insertions but deleted substantially more words. `base.en` was slightly better on the first composite, while `tiny.en` was better on the other two.

The result supports retaining `tiny.en` as the application model. The larger model did not improve accuracy on this fixed sample and imposed a higher processing cost. This is an evidence-based choice for a CPU-only student prototype rather than a claim that `tiny.en` is universally superior.

Each composite joins source-ordered utterance segments from the same meeting, speaker and headset. It is longer than the initial clips but is not an uninterrupted minute of the original meeting. Both the short pilot and longer comparison used close individual-headset audio from meeting `EN2002a`, so neither result should be generalised to noisy or far-field recordings.

## Audio-stage conclusion

Audio implementation, Windows integration, real-data WER evaluation and model selection are complete. No further AMI evaluation is planned. The two v0.5.1 score-only JSON files and their hashes will be collected from the target PC during final evidence consolidation.
