"""Generate the controlled corporate-image evaluation set.

The images use fictional people, reserved domains/IPs and standard test payment
details. They are deliberately varied so that the pipeline is not evaluated on
twenty copies of the same clean document template.
"""

from __future__ import annotations

import hashlib
import io
import json
import random
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
IMAGE_DIRECTORY = ROOT / "images"
MANIFEST_PATH = ROOT / "corporate_image_cases.jsonl"
PROVENANCE_PATH = ROOT / "corporate_image_provenance.json"
BACKGROUND_PATH = ROOT / "assets" / "office_surface.png"
SEED = 3070

FONT_CANDIDATES = {
    "sans": (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ),
    "bold": (
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ),
    "mono": (
        Path("C:/Windows/Fonts/consola.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    ),
    "hand": (
        Path("C:/Windows/Fonts/segoepr.ttf"),
        Path("C:/Windows/Fonts/comic.ttf"),
        Path("/usr/share/fonts/opentype/urw-base35/Z003-MediumItalic.otf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"),
    ),
}


@dataclass(frozen=True)
class Case:
    identifier: str
    document_class: str
    title: str
    lines: tuple[str, ...]
    expected: tuple[tuple[str, str], ...]
    style: str


CASES = (
    Case("corp-01-badge", "employee_badge", "EMPLOYEE", ("Alex Morgan", "alex.morgan@example.test", "+356 2100 1001"), (("PERSON_NAME", "Alex Morgan"), ("EMAIL_ADDRESS", "alex.morgan@example.test"), ("PHONE_NUMBER", "+356 2100 1001")), "badge"),
    Case("corp-02-visitor", "visitor_pass", "VISITOR PASS", ("Priya Shah", "Host: Daniel Lewis", "Call +356 2100 1002"), (("PERSON_NAME", "Priya Shah"), ("PERSON_NAME", "Daniel Lewis"), ("PHONE_NUMBER", "+356 2100 1002")), "badge"),
    Case("corp-03-sticky", "handwritten_note", "", ("Call Sofia Grech", "+356 2100 1003", "sofia.grech@example.test"), (("PERSON_NAME", "Sofia Grech"), ("PHONE_NUMBER", "+356 2100 1003"), ("EMAIL_ADDRESS", "sofia.grech@example.test")), "sticky"),
    Case("corp-04-meeting", "handwritten_meeting_note", "Meeting notes", ("Liam Carter - Malta", "liam.carter@example.test", "Server 192.0.2.44"), (("PERSON_NAME", "Liam Carter"), ("LOCATION_REFERENCE", "Malta"), ("EMAIL_ADDRESS", "liam.carter@example.test"), ("IP_ADDRESS", "192.0.2.44")), "notebook"),
    Case("corp-05-card", "business_card", "NORTHSTAR CONSULTING", ("Maya Patel", "maya.patel@example.test", "+356 2100 1005", "London"), (("PERSON_NAME", "Maya Patel"), ("EMAIL_ADDRESS", "maya.patel@example.test"), ("PHONE_NUMBER", "+356 2100 1005"), ("LOCATION_REFERENCE", "London")), "business_card"),
    Case("corp-06-hr", "hr_form", "EMPLOYEE CONTACT FORM", ("Name: Noah Williams", "Email: noah.williams@example.test", "Phone: +356 2100 1006", "Office: Malta"), (("PERSON_NAME", "Noah Williams"), ("EMAIL_ADDRESS", "noah.williams@example.test"), ("PHONE_NUMBER", "+356 2100 1006"), ("LOCATION_REFERENCE", "Malta")), "form"),
    Case("corp-07-expense", "expense_attachment", "EXPENSE PAYMENT NOTE", ("Claimant: Emma Clarke", "Card: 4111 1111 1111 1111", "Contact: emma.clarke@example.test"), (("PERSON_NAME", "Emma Clarke"), ("PAYMENT_CARD_NUMBER", "4111 1111 1111 1111"), ("EMAIL_ADDRESS", "emma.clarke@example.test")), "receipt"),
    Case("corp-08-incident", "incident_report", "INCIDENT REPORT", ("Reported by: Oliver King", "Callback: +356 2100 1008", "Device IP: 198.51.100.18", "Location: London"), (("PERSON_NAME", "Oliver King"), ("PHONE_NUMBER", "+356 2100 1008"), ("IP_ADDRESS", "198.51.100.18"), ("LOCATION_REFERENCE", "London")), "form_photo"),
    Case("corp-09-it", "it_access_sheet", "TEMPORARY ACCESS DETAILS", ("User: Chloe Martin", "Email: chloe.martin@example.test", "Gateway: 203.0.113.9"), (("PERSON_NAME", "Chloe Martin"), ("EMAIL_ADDRESS", "chloe.martin@example.test"), ("IP_ADDRESS", "203.0.113.9")), "terminal"),
    Case("corp-10-label", "courier_label", "INTERNAL COURIER", ("For: Ethan Walker", "Contact: +356 2100 1010", "Destination: Malta"), (("PERSON_NAME", "Ethan Walker"), ("PHONE_NUMBER", "+356 2100 1010"), ("LOCATION_REFERENCE", "Malta")), "label"),
    Case("corp-11-whiteboard", "whiteboard_photo", "TODAY", ("Ask Grace Taylor", "grace.taylor@example.test", "Room call +356 2100 1011"), (("PERSON_NAME", "Grace Taylor"), ("EMAIL_ADDRESS", "grace.taylor@example.test"), ("PHONE_NUMBER", "+356 2100 1011")), "whiteboard"),
    Case("corp-12-signin", "sign_in_sheet", "VISITOR SIGN-IN", ("Aiden Brown", "aiden.brown@example.test", "+356 2100 1012", "Malta"), (("PERSON_NAME", "Aiden Brown"), ("EMAIL_ADDRESS", "aiden.brown@example.test"), ("PHONE_NUMBER", "+356 2100 1012"), ("LOCATION_REFERENCE", "Malta")), "table"),
    Case("corp-13-contacts", "contact_sheet", "PROJECT CONTACTS", ("Zara Evans | +356 2100 1013", "zara.evans@example.test", "Leo Harris | 192.0.2.73"), (("PERSON_NAME", "Zara Evans"), ("PHONE_NUMBER", "+356 2100 1013"), ("EMAIL_ADDRESS", "zara.evans@example.test"), ("PERSON_NAME", "Leo Harris"), ("IP_ADDRESS", "192.0.2.73")), "sheet"),
    Case("corp-14-finance", "finance_form", "BANK PAYMENT APPROVAL", ("Approver: Ava Robinson", "IBAN: GB82 WEST 1234 5698 7654 32", "ava.robinson@example.test"), (("PERSON_NAME", "Ava Robinson"), ("IBAN", "GB82 WEST 1234 5698 7654 32"), ("EMAIL_ADDRESS", "ava.robinson@example.test")), "form"),
    Case("corp-15-callback", "handwritten_callback_note", "", ("Ben Scott called", "+356 2100 1015", "ben.scott@example.test"), (("PERSON_NAME", "Ben Scott"), ("PHONE_NUMBER", "+356 2100 1015"), ("EMAIL_ADDRESS", "ben.scott@example.test")), "sticky_photo"),
    Case("corp-16-security", "security_return_form", "BADGE RETURN", ("Employee: Mia Turner", "Contact: mia.turner@example.test", "Office: London"), (("PERSON_NAME", "Mia Turner"), ("EMAIL_ADDRESS", "mia.turner@example.test"), ("LOCATION_REFERENCE", "London")), "form_photo"),
    Case("corp-17-fax", "fax_cover", "CONFIDENTIAL FAX", ("To: Lucas Hall", "Fax: +356 2100 1017", "Email: lucas.hall@example.test"), (("PERSON_NAME", "Lucas Hall"), ("PHONE_NUMBER", "+356 2100 1017"), ("EMAIL_ADDRESS", "lucas.hall@example.test")), "fax"),
    Case("corp-18-training", "attendance_sheet", "TRAINING ATTENDANCE", ("Amelia Young", "amelia.young@example.test", "Malta", "+356 2100 1018"), (("PERSON_NAME", "Amelia Young"), ("EMAIL_ADDRESS", "amelia.young@example.test"), ("LOCATION_REFERENCE", "Malta"), ("PHONE_NUMBER", "+356 2100 1018")), "table_photo"),
    Case("corp-19-handover", "asset_handover", "LAPTOP HANDOVER", ("Assigned to: Jack Allen", "Support: jack.allen@example.test", "Laptop IP: 198.51.100.91"), (("PERSON_NAME", "Jack Allen"), ("EMAIL_ADDRESS", "jack.allen@example.test"), ("IP_ADDRESS", "198.51.100.91")), "form"),
    Case("corp-20-emergency", "emergency_contact_card", "EMERGENCY CONTACT", ("Isla Wright", "+356 2100 1020", "isla.wright@example.test", "London"), (("PERSON_NAME", "Isla Wright"), ("PHONE_NUMBER", "+356 2100 1020"), ("EMAIL_ADDRESS", "isla.wright@example.test"), ("LOCATION_REFERENCE", "London")), "wallet_card"),
)


def _font(family: str, size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES[family]:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    raise RuntimeError(f"No suitable {family} font was found on this computer.")


def _wrap(draw: ImageDraw.ImageDraw, value: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    words = value.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _background(size: tuple[int, int]) -> Image.Image:
    if BACKGROUND_PATH.is_file():
        with Image.open(BACKGROUND_PATH) as source:
            return source.convert("RGB").resize(size)
    return Image.new("RGB", size, "#d7d8d8")


def _paper_photo(case: Case, rng: random.Random, *, sticky: bool = False) -> Image.Image:
    canvas = _background((1400, 1000))
    paper_size = (930, 650) if not sticky else (700, 600)
    paper_color = "#fff4a8" if sticky else "#f8f6ef"
    paper = Image.new("RGBA", paper_size, paper_color)
    draw = ImageDraw.Draw(paper)
    title_font = _font("hand" if sticky else "bold", 58 if sticky else 42)
    body_font = _font("hand" if sticky else "sans", 48 if sticky else 36)
    y = 60
    if case.title:
        draw.text((70, y), case.title, fill="#1c2b39", font=title_font)
        y += 90
    for line in case.lines:
        for wrapped in _wrap(draw, line, body_font, paper_size[0] - 140):
            draw.text((70, y), wrapped, fill="#17212b", font=body_font)
            y += 62 if sticky else 54
        y += 10
    angle = rng.uniform(-5.5, 5.5)
    paper = paper.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
    shadow = Image.new("RGBA", paper.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((18, 18, paper.width - 5, paper.height - 5), 10, fill=(0, 0, 0, 85))
    shadow = shadow.filter(ImageFilter.GaussianBlur(16))
    x = (canvas.width - paper.width) // 2 + rng.randint(-40, 40)
    y0 = (canvas.height - paper.height) // 2 + rng.randint(-25, 25)
    canvas.paste(shadow, (x + 12, y0 + 18), shadow)
    canvas.paste(paper, (x, y0), paper)
    return canvas


def _badge(case: Case, rng: random.Random) -> Image.Image:
    canvas = _background((1400, 1000))
    badge = Image.new("RGBA", (850, 530), "#f8fbff")
    draw = ImageDraw.Draw(badge)
    draw.rounded_rectangle((4, 4, 846, 526), 32, outline="#29435c", width=8)
    draw.rectangle((0, 0, 850, 110), fill="#234d70")
    draw.text((50, 24), case.title, fill="white", font=_font("bold", 48))
    draw.ellipse((55, 160, 245, 350), fill="#cbd6df", outline="#587083", width=4)
    draw.ellipse((112, 188, 188, 264), fill="#8da1b1")
    draw.pieslice((82, 245, 218, 382), 180, 360, fill="#8da1b1")
    y = 155
    for index, line in enumerate(case.lines):
        font = _font("bold" if index == 0 else "sans", 48 if index == 0 else 34)
        draw.text((300, y), line, fill="#162330", font=font)
        y += 92
    badge = badge.rotate(rng.uniform(-3, 3), expand=True, resample=Image.Resampling.BICUBIC)
    canvas.paste(badge, ((canvas.width - badge.width) // 2, (canvas.height - badge.height) // 2), badge)
    return canvas


def _clean_document(case: Case, rng: random.Random) -> Image.Image:
    width, height = (1200, 900)
    if case.style in {"business_card", "wallet_card"}:
        width, height = (1200, 700)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    accent = "#1f4e79"
    draw.rectangle((0, 0, width, 120), fill=accent)
    draw.text((70, 32), case.title, fill="white", font=_font("bold", 48))
    y = 190
    font_family = "mono" if case.style == "terminal" else "sans"
    for line in case.lines:
        font = _font(font_family, 42 if case.style != "receipt" else 38)
        draw.text((90, y), line, fill="#101820", font=font)
        draw.line((90, y + 58, width - 90, y + 58), fill="#d4dce4", width=2)
        y += 105
    if case.style in {"table", "table_photo", "sheet"}:
        for line_y in range(165, height - 50, 92):
            draw.line((55, line_y, width - 55, line_y), fill="#9daab4", width=2)
        draw.rectangle((55, 155, width - 55, height - 55), outline="#6d7d89", width=3)
    if case.style in {"form", "fax", "label"}:
        draw.rectangle((55, 155, width - 55, height - 55), outline="#677783", width=3)
    if "photo" in case.style:
        image = image.rotate(rng.uniform(-3.5, 3.5), expand=True, fillcolor="#d4d6d8", resample=Image.Resampling.BICUBIC)
        image = ImageEnhance.Contrast(image).enhance(0.93)
        image = image.filter(ImageFilter.GaussianBlur(0.45))
    elif case.style in {"fax", "receipt"}:
        image = image.convert("L").filter(ImageFilter.GaussianBlur(0.35)).convert("RGB")
    return image


def _render(case: Case) -> Image.Image:
    rng = random.Random(f"{SEED}:{case.identifier}")
    if case.style == "badge":
        image = _badge(case, rng)
    elif case.style in {"sticky", "sticky_photo", "notebook", "whiteboard"}:
        image = _paper_photo(case, rng, sticky=case.style in {"sticky", "sticky_photo"})
    elif case.style == "form_photo":
        image = _paper_photo(case, rng)
    else:
        image = _clean_document(case, rng)
    if case.style in {"whiteboard", "label"}:
        image = image.filter(ImageFilter.GaussianBlur(0.7))
    return image.convert("RGB")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    IMAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    provenance_rows = []
    for case in CASES:
        image_path = IMAGE_DIRECTORY / f"{case.identifier}.png"
        image = _render(case)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", compress_level=6)
        image_path.write_bytes(buffer.getvalue())
        image.close()
        reference_text = "\n".join(part for part in (case.title, *case.lines) if part)
        manifest_rows.append(
            {
                "id": case.identifier,
                "dataset": "Controlled corporate image set v1",
                "document_class": case.document_class,
                "image_path": f"images/{image_path.name}",
                "reference_text": reference_text,
                "expected": [
                    {"finding_type": finding_type, "value": value}
                    for finding_type, value in case.expected
                ],
                "annotation_status": "labelled",
                "data_status": "fictional synthetic test data",
            }
        )
        provenance_rows.append(
            {
                "id": case.identifier,
                "document_class": case.document_class,
                "image_sha256": _sha256(image_path),
            }
        )
    MANIFEST_PATH.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in manifest_rows),
        encoding="utf-8",
    )
    PROVENANCE_PATH.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "name": "Controlled corporate image set v1",
                "seed": SEED,
                "case_count": len(CASES),
                "purpose": "Controlled OCR and end-to-end finding evaluation",
                "content": "Fictional identifiers and reserved test values only",
                "generator": Path(__file__).name,
                "background_asset": str(BACKGROUND_PATH.relative_to(ROOT)),
                "background_sha256": _sha256(BACKGROUND_PATH) if BACKGROUND_PATH.is_file() else None,
                "cases": provenance_rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Generated {len(CASES)} corporate image cases.")
    print(f"Manifest: {MANIFEST_PATH}")
    print(f"Provenance: {PROVENANCE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
