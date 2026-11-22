from pathlib import Path

from pptx import Presentation


deck = Path(__file__).with_name("智训引擎答辩.pptx")
if not deck.is_file():
    raise SystemExit("presentation file is missing")
if deck.stat().st_size >= 10 * 1024 * 1024:
    raise SystemExit("presentation exceeds 10 MiB")

presentation = Presentation(str(deck))
if len(presentation.slides) != 10:
    raise SystemExit(f"expected 10 slides, found {len(presentation.slides)}")

text_items = []
for slide in presentation.slides:
    for shape in slide.shapes:
        if getattr(shape, "has_text_frame", False) and shape.text:
            text_items.append(shape.text)
        if getattr(shape, "has_table", False):
            text_items.extend(
                cell.text
                for row in shape.table.rows
                for cell in row.cells
            )
text = "\n".join(text_items)
required = (
    "训练前",
    "训练后",
    "0.7140",
    "656.35",
    "Median PSI",
    "118",
    "40.2",
    "正式评分",
)
missing = [item for item in required if item not in text]
if missing:
    raise SystemExit("deck text missing required content: " + ", ".join(missing))

print(f"OK: {len(presentation.slides)} slides, {deck.stat().st_size} bytes")
