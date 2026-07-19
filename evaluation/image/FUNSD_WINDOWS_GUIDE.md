# v0.6.0 Windows FUNSD image evaluation

This procedure selects 25 real scanned forms, evaluates Tesseract OCR and writes
a score-only JSON file. Do not upload or include the raw forms or reference text
in the report.

## 1. Install and verify v0.6.0

Open PowerShell in the extracted project directory and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup.ps1
.\.venv\Scripts\Activate.ps1
python -m pytest
```

The setup script must finish successfully before continuing.

## 2. Download FUNSD from the official project

Read the research-use terms and download `dataset.zip` from:

<https://guillaumejaume.github.io/FUNSD/download/>

Extract it to:

```text
C:\datasets\funsd
```

The extracted directory may contain an additional `dataset` directory. The
preparation command handles both layouts.

Verify the test images and annotations:

```powershell
Get-ChildItem "C:\datasets\funsd" -Directory -Recurse -Filter testing_data |
  Select-Object -First 5 FullName

Get-ChildItem "C:\datasets\funsd" -File -Recurse -Filter *.png |
  Select-Object -First 5 FullName, Length
```

## 3. Prepare the fixed 25-document subset

Run:

```powershell
gdpr-prepare-funsd `
  --dataset "C:\datasets\funsd" `
  --out "evaluation_private\funsd" `
  --limit 25
```

Expected final lines:

```text
Selected 25 FUNSD test documents.
Private manifest: evaluation_private\funsd\funsd_test_cases.jsonl
Provenance: evaluation_private\funsd\funsd_test_provenance.json
```

Confirm the count without displaying private reference text:

```powershell
(Get-Content "evaluation_private\funsd\funsd_test_cases.jsonl").Count
Get-Content "evaluation_private\funsd\funsd_test_provenance.json"
```

The count must be `25`. The provenance file records source paths, selection
rules and SHA-256 hashes.

## 4. Validate the image evaluator

```powershell
New-Item -ItemType Directory -Force "evaluation\results" | Out-Null

gdpr-evaluate-image `
  --dataset "evaluation\image\sample_image_cases.jsonl" `
  --json-out "evaluation\results\sample_image_metrics.json"
```

This is a synthetic harness check only. It should normally report CER `0.0000`
for the supplied clear document.

## 5. Run the real 25-document evaluation

```powershell
gdpr-evaluate-image `
  --dataset "evaluation_private\funsd\funsd_test_cases.jsonl" `
  --json-out "evaluation\results\funsd_test_25_metrics.json"
```

Keep the complete terminal output. The final `AGGREGATE` row is the formal
pilot result. Lower CER is better.

## 6. Test the normal user-file route

Select the first prepared image and scan it as a user-provided file:

```powershell
$FirstImage = Get-ChildItem "evaluation_private\funsd\images" -File |
  Sort-Object Name |
  Select-Object -First 1

gdpr-scan `
  --file $FirstImage.FullName `
  --json-out "evaluation\results\funsd_user_scan.json"
```

This second command is not the CER evaluation. It demonstrates the actual app
route: user image, OCR, personal-data detection and exposure indicator.

## 7. Preserve report evidence

Keep these files on the project machine:

```text
evaluation\results\sample_image_metrics.json
evaluation\results\funsd_test_25_metrics.json
evaluation\results\funsd_user_scan.json
evaluation_private\funsd\funsd_test_provenance.json
```

Also keep screenshots of:

1. the successful automated-test total;
2. the 25-document preparation confirmation;
3. the final aggregate CER row;
4. one normal user-image scan showing the exposure score.

Do not screenshot the raw forms, reference text or finding values. We will
collect SHA-256 hashes and write the final result into the report evidence log
after the Windows run.
