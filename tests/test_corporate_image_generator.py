import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image


GENERATOR = (
    Path(__file__).parents[1]
    / "evaluation"
    / "image"
    / "corporate_synthetic"
    / "generate_corporate_images.py"
)


def _generator_module():
    spec = importlib.util.spec_from_file_location("corporate_generator", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_controlled_set_contains_20_readable_labelled_images() -> None:
    module = _generator_module()
    rows = [json.loads(line) for line in module.MANIFEST_PATH.read_text().splitlines()]
    assert len(rows) == 20
    assert len({row["document_class"] for row in rows}) == 20
    assert all(row["annotation_status"] == "labelled" for row in rows)
    assert all(row["expected"] for row in rows)
    for row in rows:
        with Image.open(module.ROOT / row["image_path"]) as image:
            image.verify()


def test_controlled_set_uses_only_reserved_test_domains() -> None:
    module = _generator_module()
    rows = [json.loads(line) for line in module.MANIFEST_PATH.read_text().splitlines()]
    emails = [
        item["value"]
        for row in rows
        for item in row["expected"]
        if item["finding_type"] == "EMAIL_ADDRESS"
    ]
    assert emails
    assert all(email.endswith("@example.test") for email in emails)
