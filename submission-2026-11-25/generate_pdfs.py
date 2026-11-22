from pathlib import Path
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
FONT_REGULAR = "MicrosoftYaHei"
FONT_BOLD = "MicrosoftYaHei-Bold"
FONT_MONO = "Courier"
INK = colors.HexColor("#183247")
TEAL = colors.HexColor("#177E89")
ORANGE = colors.HexColor("#D97A34")
PALE = colors.HexColor("#EAF1F4")
GRID = colors.HexColor("#C9D5DB")


def register_fonts():
    regular = Path(r"C:\Windows\Fonts\msyh.ttc")
    bold = Path(r"C:\Windows\Fonts\msyhbd.ttc")
    pdfmetrics.registerFont(TTFont(FONT_REGULAR, str(regular), subfontIndex=0))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, str(bold), subfontIndex=0))
    pdfmetrics.registerFontFamily(
        FONT_REGULAR,
        normal=FONT_REGULAR,
        bold=FONT_BOLD,
        italic=FONT_REGULAR,
        boldItalic=FONT_BOLD,
    )


def inline_markup(text):
    parts = re.split(r"(`[^`]+`|\*\*.*?\*\*)", text)
    output = []
    for part in parts:
        if part.startswith("`") and part.endswith("`"):
            output.append(
                f'<font name="{FONT_MONO}" color="#177E89">{escape(part[1:-1])}</font>'
            )
        elif part.startswith("**") and part.endswith("**"):
            output.append(f"<b>{escape(part[2:-2])}</b>")
        else:
            output.append(escape(part))
    return "".join(output)


def make_styles():
    return {
        "title": ParagraphStyle(
            "TitleCN",
            fontName=FONT_BOLD,
            fontSize=22,
            leading=29,
            textColor=INK,
            spaceAfter=9 * mm,
            alignment=TA_LEFT,
        ),
        "h1": ParagraphStyle(
            "HeadingCN",
            fontName=FONT_BOLD,
            fontSize=15,
            leading=20,
            textColor=TEAL,
            spaceBefore=5 * mm,
            spaceAfter=2.4 * mm,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "SubheadingCN",
            fontName=FONT_BOLD,
            fontSize=11.5,
            leading=16,
            textColor=INK,
            spaceBefore=3 * mm,
            spaceAfter=1.5 * mm,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "BodyCN",
            fontName=FONT_REGULAR,
            fontSize=9.3,
            leading=14.2,
            textColor=colors.HexColor("#263540"),
            spaceAfter=2.2 * mm,
            wordWrap="CJK",
        ),
        "bullet": ParagraphStyle(
            "BulletCN",
            fontName=FONT_REGULAR,
            fontSize=9.1,
            leading=13.7,
            leftIndent=12,
            firstLineIndent=-8,
            textColor=colors.HexColor("#263540"),
            spaceAfter=1.4 * mm,
            wordWrap="CJK",
        ),
        "table": ParagraphStyle(
            "TableCN",
            fontName=FONT_REGULAR,
            fontSize=7.4,
            leading=10,
            textColor=colors.HexColor("#263540"),
            wordWrap="CJK",
        ),
        "table_header": ParagraphStyle(
            "TableHeaderCN",
            fontName=FONT_BOLD,
            fontSize=7.5,
            leading=10,
            textColor=colors.white,
            alignment=TA_CENTER,
            wordWrap="CJK",
        ),
        "code": ParagraphStyle(
            "CodeCN",
            fontName=FONT_MONO,
            fontSize=7.4,
            leading=10,
            backColor=PALE,
            borderColor=GRID,
            borderWidth=0.5,
            borderPadding=5,
            leftIndent=4,
            rightIndent=4,
            spaceBefore=1.5 * mm,
            spaceAfter=3 * mm,
        ),
    }


def parse_table(lines, styles, available_width):
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and all(re.fullmatch(r"[:\-\s]+", cell or "-") for cell in cells):
            continue
        rows.append(cells)
    if not rows:
        return None
    columns = max(len(row) for row in rows)
    data = []
    for row_index, row in enumerate(rows):
        row = row + [""] * (columns - len(row))
        style = styles["table_header"] if row_index == 0 else styles["table"]
        data.append([Paragraph(inline_markup(cell), style) for cell in row])
    table = Table(
        data,
        colWidths=[available_width / columns] * columns,
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("GRID", (0, 0), (-1, -1), 0.45, GRID),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def build_story(markdown_path, doc):
    styles = make_styles()
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    story = []
    i = 0
    in_code = False
    code_lines = []
    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("```"):
            if in_code:
                story.append(
                    Preformatted("\n".join(code_lines), styles["code"])
                )
                code_lines = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue
        if not line.strip() or line.strip() == "---":
            story.append(Spacer(1, 1.3 * mm))
            i += 1
            continue
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            table = parse_table(table_lines, styles, doc.width)
            if table is not None:
                story.extend([Spacer(1, 1.5 * mm), table, Spacer(1, 3 * mm)])
            continue
        if line.startswith("# "):
            story.append(Paragraph(inline_markup(line[2:]), styles["title"]))
        elif line.startswith("## "):
            story.append(Paragraph(inline_markup(line[3:]), styles["h1"]))
        elif line.startswith("### "):
            story.append(Paragraph(inline_markup(line[4:]), styles["h2"]))
        elif line.startswith("- "):
            story.append(
                Paragraph("• " + inline_markup(line[2:]), styles["bullet"])
            )
        elif re.match(r"^\d+\.\s+", line):
            content = re.sub(r"^\d+\.\s+", "", line)
            story.append(
                Paragraph("• " + inline_markup(content), styles["bullet"])
            )
        else:
            story.append(Paragraph(inline_markup(line), styles["body"]))
        i += 1
    if code_lines:
        story.append(Preformatted("\n".join(code_lines), styles["code"]))
    return story


def page_chrome(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.6)
    canvas.line(doc.leftMargin, height - 18 * mm, width - doc.rightMargin, height - 18 * mm)
    canvas.setFont(FONT_REGULAR, 7.5)
    canvas.setFillColor(TEAL)
    canvas.drawString(doc.leftMargin, height - 14 * mm, "智训引擎｜工业制造模型训练与受控优化")
    canvas.setFillColor(colors.HexColor("#677985"))
    canvas.drawRightString(width - doc.rightMargin, height - 14 * mm, "开发验证稿 · 2026-11-21")
    canvas.line(doc.leftMargin, 14 * mm, width - doc.rightMargin, 14 * mm)
    canvas.drawString(doc.leftMargin, 9 * mm, "公开数据本地实验参考；非平台正式评分")
    canvas.drawRightString(width - doc.rightMargin, 9 * mm, f"第 {doc.page} 页")
    canvas.restoreState()


def create_pdf(markdown_name, pdf_name):
    source = ROOT / "docs" / markdown_name
    output = ROOT / "docs" / pdf_name
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=25 * mm,
        bottomMargin=21 * mm,
        title=source.stem,
        author="智训引擎参赛团队",
    )
    doc.build(
        build_story(source, doc),
        onFirstPage=page_chrome,
        onLaterPages=page_chrome,
    )
    print(f"{output.name}: {output.stat().st_size} bytes")


if __name__ == "__main__":
    register_fonts()
    create_pdf("system_run_instructions.md", "system_run_instructions.pdf")
    create_pdf("project_description.md", "project_description.pdf")
