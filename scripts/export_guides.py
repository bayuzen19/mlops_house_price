"""Create printable guides from the Markdown sources (requires the docs extra)."""

import re
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf"
INK = colors.HexColor("#183746")
TEAL = colors.HexColor("#087E8B")
PALE = colors.HexColor("#F0F5F7")


def register_fonts():
    candidates = [
        (Path("C:/Windows/Fonts"), "arial.ttf", "arialbd.ttf", "consola.ttf"),
        (
            Path("/usr/share/fonts/truetype/dejavu"),
            "DejaVuSans.ttf",
            "DejaVuSans-Bold.ttf",
            "DejaVuSansMono.ttf",
        ),
    ]
    for folder, regular, bold, mono in candidates:
        if all((folder / name).exists() for name in (regular, bold, mono)):
            for family, filename in zip(
                ("Body", "BodyBold", "Mono"), (regular, bold, mono), strict=True
            ):
                pdfmetrics.registerFont(TTFont(family, str(folder / filename)))
            pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyBold")
            return "Body", "BodyBold", "Mono"
    return "Helvetica", "Helvetica-Bold", "Courier"


BODY, BOLD, MONO = register_fonts()
styles = getSampleStyleSheet()
styles.add(ParagraphStyle("Text", fontName=BODY, fontSize=9.2, leading=13.4, spaceAfter=7))
styles.add(
    ParagraphStyle(
        "Section",
        fontName=BOLD,
        fontSize=16,
        leading=21,
        textColor=INK,
        spaceBefore=8,
        spaceAfter=13,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        "Subsection",
        fontName=BOLD,
        fontSize=11.4,
        leading=15,
        textColor=TEAL,
        spaceBefore=10,
        spaceAfter=7,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        "CodeBlock",
        fontName=MONO,
        fontSize=7.1,
        leading=10,
        backColor=PALE,
        borderPadding=8,
        spaceBefore=7,
        spaceAfter=13,
        splitLongWords=True,
    )
)
styles.add(ParagraphStyle("Cell", fontName=BODY, fontSize=8.1, leading=11.3))
styles.add(ParagraphStyle("Cover", fontName=BOLD, fontSize=30, leading=36, textColor=INK))
styles.add(ParagraphStyle("Subtitle", fontName=BODY, fontSize=13, leading=20, textColor=TEAL))
styles.add(
    ParagraphStyle(
        "TOCItem",
        fontName=BODY,
        fontSize=10,
        leading=16,
        leftIndent=0,
        firstLineIndent=0,
        spaceBefore=5,
    )
)


def normalized(text):
    for char in ("\u2011", "\u2013", "\u2014"):
        text = text.replace(char, "-")
    return text.replace("→", " -> ").replace("≥", ">=")


def inline(text):
    text = escape(normalized(text))
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" color="#087E8B">\1</a>', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+\.md)\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", rf'<font name="{MONO}" size="8">\1</font>', text)
    return text


class GuideDoc(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "Section":
            label = flowable.getPlainText()
            key = "section-" + str(self.page)
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(label, key, level=0)
            self.notify("TOCEntry", (0, label, self.page, key))


def page_decoration(canvas, doc):
    width, height = A4
    canvas.saveState()
    canvas.setStrokeColor(TEAL)
    canvas.setLineWidth(0.7)
    canvas.line(18 * mm, height - 15 * mm, width - 18 * mm, height - 15 * mm)
    canvas.setFont(BODY, 7.5)
    canvas.setFillColor(INK)
    canvas.drawString(18 * mm, height - 12 * mm, "HOUSE PRICE / MLOPS CLASSROOM")
    canvas.drawString(18 * mm, 12 * mm, "github.com/bayuzen19/mlops_house_price")
    canvas.drawRightString(width - 18 * mm, 12 * mm, str(doc.page))
    canvas.restoreState()


def markdown_story(source, width):
    lines = source.splitlines()
    story = []
    index = 0
    seen_section = False
    while index < len(lines):
        line = lines[index].strip()
        if not line or line.startswith("# "):
            index += 1
            continue
        if line.startswith("## "):
            if seen_section:
                story.append(PageBreak())
            story.append(Paragraph(inline(line[3:]), styles["Section"]))
            seen_section = True
        elif line.startswith("### "):
            story.append(Paragraph(inline(line[4:]), styles["Subsection"]))
        elif line.startswith("```"):
            language = line[3:]
            code = []
            index += 1
            while index < len(lines) and not lines[index].startswith("```"):
                code.append(lines[index])
                index += 1
            if language == "mermaid":
                story.append(
                    Paragraph(
                        "<b>Alur model:</b> CSV -> DVC/Git -> training -> MLflow -> prediksi.<br/>"
                        "<b>Alur delivery:</b> push/PR -> CI -> uji container -> GHCR.",
                        styles["Text"],
                    )
                )
            else:
                text = "<br/>".join(
                    escape(normalized(row)).replace("  ", "&nbsp;&nbsp;") for row in code
                )
                story.append(Paragraph(text, styles["CodeBlock"]))
        elif line.startswith("|"):
            rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                entries = [part.strip() for part in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[:\- ]+", item) for item in entries):
                    rows.append([Paragraph(inline(item), styles["Cell"]) for item in entries])
                index += 1
            count = len(rows[0])
            ratios = {2: [0.33, 0.67], 3: [0.25, 0.31, 0.44], 4: [0.25] * 4}[count]
            table = Table(
                rows, colWidths=[width * ratio for ratio in ratios], repeatRows=1, hAlign=TA_LEFT
            )
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D7E9ED")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 7),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                        ("TOPPADDING", (0, 0), (-1, -1), 7),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                        ("LINEBELOW", (0, 0), (-1, 0), 0.5, TEAL),
                    ]
                )
            )
            story.extend([table, Spacer(1, 10)])
            continue
        else:
            paragraph = [line]
            while index + 1 < len(lines) and lines[index + 1].strip():
                following = lines[index + 1].strip()
                if following.startswith(("#", "```", "|", "- ")) or re.match(r"\d+\. ", following):
                    break
                paragraph.append(following)
                index += 1
            story.append(Paragraph(inline(" ".join(paragraph)), styles["Text"]))
        index += 1
    return story


def export(source, title, subtitle, output_name):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / output_name
    doc = GuideDoc(
        str(path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=23 * mm,
        bottomMargin=22 * mm,
        title=title,
        author="House Price MLOps Classroom",
    )
    toc = TableOfContents()
    toc.levelStyles = [styles["TOCItem"]]
    story = [
        Spacer(1, 35 * mm),
        Paragraph("House Price<br/>MLOps", styles["Cover"]),
        Spacer(1, 14 * mm),
        Paragraph(title, styles["Subtitle"]),
        Spacer(1, 10 * mm),
        Paragraph(subtitle, styles["Text"]),
        Spacer(1, 15 * mm),
        Paragraph(
            "Python 3.13 / DVC / MLflow / Docker / GitHub Actions / GHCR",
            styles["Text"],
        ),
        Paragraph(
            "Repository dan sumber editable tersedia di GitHub. "
            "Salin perintah panjang dari Markdown agar baris perintah tetap utuh.",
            styles["Text"],
        ),
        PageBreak(),
        Paragraph("Daftar isi", styles["Section"]),
        toc,
        PageBreak(),
    ]
    story += markdown_story(source.read_text(encoding="utf-8"), doc.width)
    doc.multiBuild(story, onFirstPage=page_decoration, onLaterPages=page_decoration)
    print(path)


if __name__ == "__main__":
    export(
        ROOT / "docs/PANDUAN_MENGAJAR.md",
        "Panduan mengajar",
        "Panduan lengkap 23 tahap notebook: kode, penjelasan, hasil, "
        "lalu modul, DVC, Docker, dan CI/CD.",
        "Panduan_Mengajar_MLOps_House_Price.pdf",
    )
    export(
        ROOT / "docs/LATIHAN_PESERTA.md",
        "Lembar latihan peserta",
        "Praktik notebook dan server, tujuh latihan lanjutan, "
        "tabel bukti, dan kunci diskusi pengajar.",
        "Lembar_Latihan_MLOps_House_Price.pdf",
    )
