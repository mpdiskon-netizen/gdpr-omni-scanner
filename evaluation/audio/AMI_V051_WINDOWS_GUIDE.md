# v0.5.1 AMI one-minute comparison — Windows steps

## What this step adds

This is the final planned audio experiment:

- three deterministic AMI composites, each containing about one minute of speech;
- the same files tested with Whisper `tiny.en` and `base.en`;
- WER, processing seconds and real-time factor recorded automatically.

The files are same-speaker composites assembled from official AMI utterance segments. They are useful longer inputs, but they are not uninterrupted one-minute meeting recordings.

## 1. Install and test v0.5.1

Extract the v0.5.1 ZIP, open PowerShell in the folder containing `pyproject.toml`, and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
.\.venv\Scripts\Activate.ps1
python -m pytest
```

Expected: `57 passed`.

## 2. Preserve the completed v0.5.0 pilot files

Do not delete the old v0.5.0 folder yet. Copy these two report-safe files from it into the new build if they exist:

```powershell
New-Item -ItemType Directory -Force "evaluation\results" | Out-Null

$OldProject = "C:\Users\Konstantinos\Desktop\CM 3070\gdpr-omni-scanner-v0.5.0\gdpr-omni-scanner-v0.5.0"

Test-Path "$OldProject\evaluation\results\ami_ihm_5_metrics.json"
Test-Path "$OldProject\evaluation\results\ami_windows_evidence.txt"

Copy-Item "$OldProject\evaluation\results\ami_ihm_5_metrics.json" `
  "evaluation\results\ami_ihm_5_metrics.json" -ErrorAction SilentlyContinue

Copy-Item "$OldProject\evaluation\results\ami_windows_evidence.txt" `
  "evaluation\results\ami_windows_evidence.txt" -ErrorAction SilentlyContinue
```

Both `Test-Path` commands should print `True`. If your old folder has a different location, change only the `$OldProject` value. Do not copy raw reference transcripts into the public `evaluation` folder.

## 3. Create the separate AMI helper environment

Leave the scanner environment and create the small dataset-preparation environment:

```powershell
deactivate
py -3.11 -m venv .ami-tools
.\.ami-tools\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install "datasets==2.21.0" "soundfile==0.12.1" "librosa==0.10.2.post1"
```

## 4. Prepare three roughly one-minute composites

```powershell
python .\evaluation\audio\prepare_ami_minute_sample.py `
  --out "evaluation_private\ami_minute" `
  --limit 3 `
  --target-seconds 60
```

This streams the AMI `ihm` test split and creates:

```text
evaluation_private\ami_minute\ami_minute_cases.jsonl
evaluation_private\ami_minute\ami_minute_provenance.json
evaluation_private\ami_minute\clips\*.wav
```

Confirm that three files were created without printing private transcripts:

```powershell
(Get-Content "evaluation_private\ami_minute\ami_minute_cases.jsonl").Count
Get-ChildItem "evaluation_private\ami_minute\clips" -Filter *.wav |
  Select-Object Name, Length
```

Expected manifest count: `3`.

## 5. Download the optional comparison model once

Return to the scanner environment, then download `base.en` before timing the evaluation. Internet is needed only for this one-time model download.

```powershell
deactivate
.\.venv\Scripts\Activate.ps1
python -c "import whisper; whisper.load_model('base.en', device='cpu'); print('base.en ready')"
```

The normal user application still defaults to `tiny.en`. `base.en` is added only for the controlled comparison.

## 6. Scan one longer file as a normal user input

```powershell
$FirstMinute = Get-ChildItem "evaluation_private\ami_minute\clips" -Filter *.wav |
  Select-Object -First 1

gdpr-scan --file $FirstMinute.FullName --show-extracted-text
```

This proves that a user-supplied longer WAV follows the normal route: Whisper transcription, personal-data detection and the exposure indicator. A score of zero is possible when the speech contains no supported personal data.

## 7. Run the controlled model comparison

```powershell
New-Item -ItemType Directory -Force "evaluation\results" | Out-Null

gdpr-evaluate-audio `
  --dataset "evaluation_private\ami_minute\ami_minute_cases.jsonl" `
  --model tiny.en `
  --json-out "evaluation\results\ami_minute_tiny_metrics.json"

gdpr-evaluate-audio `
  --dataset "evaluation_private\ami_minute\ami_minute_cases.jsonl" `
  --model base.en `
  --json-out "evaluation\results\ami_minute_base_metrics.json"
```

Each result reports WER and processing time. The first case includes loading the selected model into memory. Both commands use the same timing definition, so the comparison remains consistent.

## 8. Give the results back for interpretation

Run this compact command and send one screenshot of its output:

```powershell
python -c "import json, pathlib; paths=['evaluation/results/ami_minute_tiny_metrics.json','evaluation/results/ami_minute_base_metrics.json']; [(lambda d,p: print(pathlib.Path(p).name, 'cases=',d['case_count'], 'ref=',d['aggregate']['reference_words'], 'WER=',d['aggregate']['word_error_rate'], 'seconds=',d['aggregate']['total_processing_seconds'], 'RTF=',d['aggregate'].get('real_time_factor')))(json.loads(pathlib.Path(p).read_text(encoding='utf-8')),p) for p in paths]"
```

Also keep privately:

```powershell
Get-FileHash "evaluation_private\ami_minute\ami_minute_provenance.json" -Algorithm SHA256
Get-FileHash "evaluation\results\ami_minute_tiny_metrics.json" -Algorithm SHA256
Get-FileHash "evaluation\results\ami_minute_base_metrics.json" -Algorithm SHA256
```

After these two runs, the audio evaluation can be frozen. We will choose the model using the measured accuracy/speed trade-off and move to the small image evaluation.
