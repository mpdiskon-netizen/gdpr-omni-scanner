"""Offline English speech-to-text adapter using Whisper on the CPU."""

from __future__ import annotations

import os
import shutil
from functools import lru_cache
from pathlib import Path
from typing import Any

SUPPORTED_AUDIO_SUFFIXES = {".wav", ".mp3"}
MAX_AUDIO_BYTES = 50 * 1024 * 1024
WHISPER_MODEL_NAME = "tiny.en"
SUPPORTED_WHISPER_MODELS = ("tiny.en", "base.en")


class AudioUnavailableError(RuntimeError):
    """Raised when Whisper, FFmpeg or the local model is unavailable."""


def _require_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        raise AudioUnavailableError(
            "FFmpeg is unavailable. Install FFmpeg, restart PowerShell and run "
            "ffmpeg -version."
        )


@lru_cache(maxsize=len(SUPPORTED_WHISPER_MODELS))
def load_whisper_model(model_name: str = WHISPER_MODEL_NAME) -> Any:
    """Load an approved English model once per process, explicitly on the CPU."""

    if model_name not in SUPPORTED_WHISPER_MODELS:
        supported = ", ".join(SUPPORTED_WHISPER_MODELS)
        raise ValueError(f"Supported Whisper models are: {supported}.")

    try:
        import whisper
    except ImportError as error:
        raise AudioUnavailableError(
            "Whisper is unavailable. Run setup.ps1 to install the audio dependencies."
        ) from error

    download_root = os.environ.get("GDPR_SCANNER_WHISPER_CACHE")
    try:
        return whisper.load_model(
            model_name,
            device="cpu",
            download_root=download_root,
        )
    except Exception as error:
        raise AudioUnavailableError(
            f"The Whisper {model_name} model could not be loaded. Connect once to "
            "download it, then retry."
        ) from error


def _whisper_version() -> str:
    try:
        import whisper

        return getattr(whisper, "__version__", "unknown")
    except ImportError:
        return "unknown"


def transcribe_audio(
    path: str | Path,
    model: Any | None = None,
    model_name: str = WHISPER_MODEL_NAME,
) -> tuple[str, str]:
    """Transcribe a local WAV/MP3 file and return text plus a model identifier."""

    input_path = Path(path)
    if input_path.suffix.casefold() not in SUPPORTED_AUDIO_SUFFIXES:
        raise ValueError("Supported audio formats are .wav and .mp3.")
    if not input_path.is_file():
        raise ValueError(f"Audio file does not exist: {input_path}")
    if input_path.stat().st_size > MAX_AUDIO_BYTES:
        raise ValueError("Audio exceeds the 50 MB size limit.")

    _require_ffmpeg()
    if model_name not in SUPPORTED_WHISPER_MODELS:
        supported = ", ".join(SUPPORTED_WHISPER_MODELS)
        raise ValueError(f"Supported Whisper models are: {supported}.")

    whisper_model = model or load_whisper_model(model_name)
    try:
        output = whisper_model.transcribe(
            str(input_path),
            language="en",
            fp16=False,
            temperature=0,
        )
    except Exception as error:
        raise AudioUnavailableError(f"Whisper transcription failed: {error}") from error

    text = str(output.get("text", "")).strip()
    if not text:
        raise ValueError("Whisper did not transcribe any speech from the audio file.")
    return text, f"whisper:{model_name}:{_whisper_version()}:cpu"
