from types import SimpleNamespace

import pytest

from gdpr_scanner import easyocr_adapter


def test_easyocr_adapter_requires_optional_package(monkeypatch, tmp_path) -> None:
    image = tmp_path / "image.png"
    image.write_bytes(b"not needed")
    monkeypatch.setattr(easyocr_adapter, "_reader", None)
    real_import = __import__

    def blocked_import(name, *args, **kwargs):
        if name == "easyocr":
            raise ImportError
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", blocked_import)
    with pytest.raises(easyocr_adapter.EasyOcrUnavailableError, match="optional"):
        easyocr_adapter._load_reader(False)


def test_easyocr_adapter_joins_detected_lines(monkeypatch, tmp_path) -> None:
    from PIL import Image

    image = tmp_path / "image.png"
    Image.new("RGB", (20, 20), "white").save(image)
    reader = SimpleNamespace(readtext=lambda *_args, **_kwargs: ["Alex Morgan", "alex@example.test"])
    monkeypatch.setattr(easyocr_adapter, "_load_reader", lambda _download: reader)
    monkeypatch.setattr(easyocr_adapter, "version", lambda _name: "1.7.2")
    text, model = easyocr_adapter.extract_easyocr_text(image)
    assert text == "Alex Morgan\nalex@example.test"
    assert model == "easyocr:en:1.7.2:cpu"
