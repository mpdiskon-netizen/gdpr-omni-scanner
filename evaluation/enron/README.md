# Enron pilot preparation

The Enron corpus is not included in this project archive. Obtain the May 7 2015 version from the official CMU page:

<https://www.cs.cmu.edu/~enron/>

After extracting the corpus locally, select 20 reproducible messages:

```powershell
gdpr-prepare-enron `
  --corpus C:\datasets\enron\maildir `
  --out evaluation_private\enron_pilot_unlabelled.jsonl `
  --limit 20
```

The selection is determined by the relative file paths and fixed seed `3070`. Each output case also records its source path and SHA-256 content hash.

The official corpus contains Unix-style filenames ending in a period, such as `1.`. Normal Windows paths cannot open these files even though PowerShell can list them. Version 0.4.2 reads them through the Windows extended-path form and they must not be renamed.

Follow `ANNOTATION_GUIDE.md` before running `gdpr-evaluate-text`. Raw messages and annotations remain private local evaluation material and are excluded from the project archive.

Version 0.4.4 provides machine-assisted human review. Start with one case:

```powershell
gdpr-annotate-enron --dataset evaluation_private\enron_pilot_unlabelled.jsonl --case 2 --assisted
```

The scanner groups its suggestions by finding type. The reviewer accepts or rejects them and then explicitly adds missed values. The original JSONL is automatically backed up the first time a label is saved.
