# Model selection record

## Purpose

The selected CM3020 template expects evidence that multiple pre-trained models were investigated, operationalised and selected for a reason. This record separates decisions already supported by implementation evidence from comparisons still requiring measurement.

## Selection criteria

1. Runs locally after one-time installation.
2. Supports English on Windows and Python 3.11.
3. Fits a single-machine university prototype.
4. Exposes outputs that can be explained and evaluated.
5. Has usable documentation, licensing information and an active software ecosystem.
6. Covers a different data domain while contributing to one integrated objective.

## Current choices

| Domain | Selected component | Role | Current evidence | Remaining comparison evidence |
|---|---|---|---|---|
| Text | spaCy `en_core_web_sm` | Named entities in direct, OCR and transcribed text | Integrated offline; unit/integration tests; real Enron pilot | Record at least one considered alternative and compare model size, speed, supported entity types and offline suitability |
| Image | Tesseract English OCR | Convert printed document images to text | Integrated offline; Windows FUNSD CER=0.3868; controlled CER=0.1039 and downstream F1=0.8000 | Complete: EasyOCR had lower CER but weaker controlled downstream F1 and substantially slower processing |
| Audio | Whisper `tiny.en` | Convert English WAV/MP3 speech to text | Integrated offline; WAV/MP3 tests; five-clip AMI WER 0.2333; controlled longer comparison: `tiny.en` WER 0.2437/8.56s versus `base.en` WER 0.2708/12.36s | Complete: `tiny.en` retained because it was both more accurate and faster on the fixed Windows sample |

## Engineering reason for the common text stage

Tesseract and Whisper produce text, after which spaCy and the deterministic identifier detectors use one common finding and scoring pipeline. This keeps the application integrated rather than presenting three unrelated model demonstrations.

## Audio decision

The `tiny.en`/`base.en` comparison used the same three AMI composites, 181.15 seconds and 517 reference words. `tiny.en` required 126 word edits compared with 140 for `base.en` and ran approximately 31% faster. This supports `tiny.en` for the CPU-only prototype. The sample was small, close-microphone and drawn from one meeting, so it does not establish universal model superiority.

## Image decision

The Tesseract/EasyOCR comparison used the same 25 FUNSD forms and the same 20
controlled corporate images. EasyOCR reduced FUNSD CER from 0.3868 to 0.3317
and controlled-image CER from 0.1039 to 0.0202, but its controlled end-to-end
finding F1 was 0.6923 compared with Tesseract's 0.8000. It also required 48.91
seconds for the controlled pipeline compared with 11.05 seconds for Tesseract.
Tesseract is retained because the application objective is downstream exposure
detection rather than OCR alone, and because it provides the smaller, faster
core installation. The controlled set is synthetic, so the result does not
establish universal Tesseract superiority.

## Remaining model-selection work

The audio and image choices are complete. The final report still needs a concise
literature-based discussion of considered text alternatives; no additional
model experiment is required. Do not claim that untested text alternatives were
experimentally rejected.
