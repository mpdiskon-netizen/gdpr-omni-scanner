import importlib.util
from pathlib import Path


SCRIPT = (
    Path(__file__).parent.parent
    / "evaluation"
    / "audio"
    / "prepare_ami_minute_sample.py"
)


def _load_helper():
    spec = importlib.util.spec_from_file_location("prepare_ami_minute_sample", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(speaker: str, audio_id: str, text: str) -> dict[str, object]:
    return {
        "meeting_id": "meeting-1",
        "speaker_id": speaker,
        "microphone_id": f"headset-{speaker}",
        "audio_id": audio_id,
        "begin_time": 0.0,
        "end_time": 1.0,
        "text": text,
        "audio": {"array": [0.1, 0.2, 0.3, 0.4], "sampling_rate": 4},
    }


def test_minute_selector_is_source_ordered_and_same_speaker() -> None:
    helper = _load_helper()
    rows = [
        _row("A", "a1", "first a"),
        _row("B", "b1", "first b"),
        _row("C", "c1", "ignored speaker"),
        _row("A", "a2", "second a"),
        _row("B", "b2", "second b"),
    ]

    groups = helper.select_composites(rows, limit=2, target_seconds=2.0)

    assert [group["speaker_id"] for group in groups] == ["A", "B"]
    assert all(group["complete"] for group in groups)
    assert [[segment["audio_id"] for segment in group["segments"]] for group in groups] == [
        ["a1", "a2"],
        ["b1", "b2"],
    ]
