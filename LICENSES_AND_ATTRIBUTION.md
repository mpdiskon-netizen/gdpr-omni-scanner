# Licences, datasets and attribution

This file records the principal external software, pretrained models and evaluation datasets used by the GDPR Omni-Scanner project.

The release repository contains project source code and small synthetic test assets. It does not redistribute the external model weights or restricted evaluation datasets listed below.

## Runtime software and models

| Component | Project use | Licence / attribution |
|---|---|---|
| spaCy and `en_core_web_sm` | English person and location recognition | MIT; <https://github.com/explosion/spaCy> and <https://github.com/explosion/spacy-models> |
| Tesseract OCR and English trained data | Printed-English document OCR | Apache License 2.0; <https://github.com/tesseract-ocr/tesseract> |
| OpenAI Whisper `tiny.en` | Offline English speech transcription | MIT; <https://github.com/openai/whisper> |
| FFmpeg | Audio decoding used by Whisper | Licence depends on build configuration; <https://ffmpeg.org/legal.html> |
| Pillow | Image loading and processing | Pillow licence; <https://github.com/python-pillow/Pillow> |
| pytesseract | Python interface to local Tesseract | Apache License 2.0; <https://github.com/madmaze/pytesseract> |
| EasyOCR 1.7.2 | Optional OCR comparison model; not the final application OCR engine | Apache License 2.0; <https://github.com/JaidedAI/EasyOCR> |

The repository does not bundle:

- the Tesseract executable;
- FFmpeg binaries;
- spaCy model packages;
- Whisper model weights;
- EasyOCR model weights;
- external runtime dependencies.

## Evaluation datasets

### Enron Email Dataset

The Enron corpus was used for a small real-email text-detection pilot.

Raw email messages and the private labelled evaluation file are not included in the public repository.

Source:

<https://www.cs.cmu.edu/~enron/>

The project used model-assisted, human-corrected labels for the supported finding categories.

### AMI Meeting Corpus

The AMI Meeting Corpus was used to evaluate Whisper transcription using word error rate and to compare `tiny.en` with `base.en`.

AMI audio and reference transcripts are not redistributed in this repository.

Source:

<https://groups.inf.ed.ac.uk/ami/corpus/>

AMI corpus material used by the project was handled under the corpus's published CC BY 4.0 conditions.

### FUNSD

FUNSD was used for OCR evaluation on real noisy scanned forms.

The project does not redistribute FUNSD images or annotations because their terms restrict redistribution of the underlying scanned documents.

Sources:

<https://guillaumejaume.github.io/FUNSD/>

<https://guillaumejaume.github.io/FUNSD/work/>

Reference:

Jaume, G., Ekenel, H. K. and Thiran, J.-P. (2019), *FUNSD: A Dataset for Form Understanding in Noisy Scanned Documents*, ICDAR-OST.

<https://arxiv.org/abs/1905.13538>

### Controlled corporate image set

The repository includes a separate controlled image dataset created for this project.

It contains fictional or reserved test values and is used to evaluate:

- OCR character error rate;
- personal-data finding precision;
- recall;
- F1;
- the complete image-to-score pipeline.

The set supplements FUNSD but is not presented as representative real-world data.

Its generator, labels, provenance information and generated images are included under:

```text
evaluation/image/corporate_synthetic/
```

## Privacy and redistribution

External evaluation material containing real-world text, audio or document images is kept outside the public repository where required.

Only privacy-safe aggregate metrics, hashes and project-created synthetic assets are included in the repository.
