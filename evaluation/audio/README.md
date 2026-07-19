# Audio evaluation

`gdpr-evaluate-audio` transcribes each local WAV/MP3 file with Whisper and compares the result with a reference transcript using word error rate (WER). v0.5.1 also records wall-clock processing time and supports a controlled choice between `tiny.en` and `base.en`.

The included one-case manifest validates the evaluation pipeline only:

```powershell
gdpr-evaluate-audio `
  --dataset evaluation\audio\sample_audio_cases.jsonl `
  --json-out evaluation\results\sample_audio_metrics.json
```

WER is calculated as `(substitutions + deletions + insertions) / reference words`. Before matching, English text is case-folded, punctuation is ignored and apostrophes are removed. The score can exceed `1.0` when insertions are numerous.

The completed five-clip AMI pilot produced WER `0.2333` on 90 reference words. See `AMI_EVALUATION_REPORT.md` for the method and limitations.

The final small extension compares both supported Whisper models on the same three roughly one-minute AMI speech composites. Follow `AMI_V051_WINDOWS_GUIDE.md`. AMI audio and reference transcripts are not included in the project archive.
