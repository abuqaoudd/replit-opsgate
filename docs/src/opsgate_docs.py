"""Shared house style and layout helpers for the OpsGate documentation PDFs.

Each build_*.py sibling assembles one document from these helpers and writes the PDF into
docs/ (the parent of this folder). Rebuild after editing:

    python3 docs/src/build_overview.py
    python3 docs/src/build_technical.py
    python3 docs/src/build_using.py

Requires reportlab (pip install reportlab).
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

DOCS_DIR = Path(__file__).resolve().parent.parent

NAVY = colors.HexColor("#1B2A4A")
NAVY_LIGHT = colors.HexColor("#3B4F76")
BOX_BG = colors.HexColor("#EEF3FA")
BOX_BORDER = colors.HexColor("#B9C7DC")
ROW_ALT = colors.HexColor("#F4F7FB")
GRID = colors.HexColor("#C9D3E0")
TEXT = colors.HexColor("#1A1A1A")
MUTED = colors.HexColor("#5B6B85")

PAGE_W, PAGE_H = letter
MARGIN = 0.85 * inch
CONTENT_W = PAGE_W - 2 * MARGIN


def _style(name, **kw):
    base = dict(fontName="Helvetica", fontSize=10, leading=14, textColor=TEXT, spaceAfter=8)
    base.update(kw)
    return ParagraphStyle(name, **base)


S_TITLE = _style("DocTitle", fontName="Helvetica-Bold", fontSize=27, leading=31, textColor=NAVY, spaceAfter=6)
S_SUBTITLE = _style("DocSubtitle", fontSize=13.5, leading=17, textColor=colors.HexColor("#33415C"), spaceAfter=10)
S_TAGLINE = _style("DocTagline", fontName="Helvetica-Oblique", fontSize=9.5, leading=13, textColor=NAVY_LIGHT, spaceAfter=2)
S_VERSION = _style("DocVersion", fontSize=9.5, leading=13, textColor=MUTED, spaceAfter=0)
S_INTRO = _style("Intro", fontSize=10.5, leading=15, spaceAfter=4)
S_H1 = _style("H1", fontName="Helvetica-Bold", fontSize=16, leading=20, textColor=NAVY, spaceBefore=16, spaceAfter=8)
S_H2 = _style("H2", fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=colors.HexColor("#22304A"), spaceBefore=10, spaceAfter=5)
S_BODY = _style("Body", fontSize=10, leading=14.5, spaceAfter=7)
S_BULLET = _style("Bullet", fontSize=10, leading=14.5, spaceAfter=4, leftIndent=14)
S_CALLOUT_TITLE = _style("CalloutTitle", fontName="Helvetica-Bold", fontSize=10.5, leading=14, textColor=NAVY, spaceAfter=4)
S_CALLOUT_BODY = _style("CalloutBody", fontSize=10, leading=14.5, spaceAfter=3)
S_TABLE_HEAD = _style("TableHead", fontName="Helvetica-Bold", fontSize=9.5, leading=12, textColor=colors.white)
S_TABLE_CELL = _style("TableCell", fontSize=9.3, leading=12.5)
S_TOC_ITEM = _style("TocItem", fontSize=10.5, leading=16)
S_FOOTNOTE = _style("Footnote", fontSize=9, leading=13, textColor=MUTED, spaceAfter=4)
S_CENTER_NOTE = ParagraphStyle("CenterNote", parent=S_FOOTNOTE, alignment=1)


def bullets(items):
    """items: plain strings, or (lead, rest) tuples rendered as a bold lead followed by a dash.

    Text is reportlab Paragraph markup: escape literal '<' and '>' as &lt; and &gt;."""
    out = []
    for item in items:
        if isinstance(item, tuple):
            lead, rest = item
            text = f"<b>{lead}</b> — {rest}" if rest else f"<b>{lead}</b>"
        else:
            text = item
        out.append(Paragraph(f"•&nbsp;&nbsp;{text}", S_BULLET))
    return out


def para(text):
    return Paragraph(text, S_BODY)


def h2(text):
    return Paragraph(text, S_H2)


def callout(title, text):
    inner = [Paragraph(title, S_CALLOUT_TITLE)]
    for chunk in (text if isinstance(text, list) else [text]):
        inner.append(Paragraph(chunk, S_CALLOUT_BODY))
    table = Table([[inner]], colWidths=[CONTENT_W])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BOX_BG),
        ("BOX", (0, 0), (-1, -1), 0.75, BOX_BORDER),
        ("LINEBEFORE", (0, 0), (0, -1), 3, NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return table


def data_table(header, rows, col_widths=None):
    data = [[Paragraph(h, S_TABLE_HEAD) for h in header]]
    data += [[Paragraph(c, S_TABLE_CELL) for c in row] for row in rows]
    if not col_widths:
        col_widths = [CONTENT_W / len(header)] * len(header)
    table = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.5, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]
    style += [("BACKGROUND", (0, i), (-1, i), ROW_ALT) for i in range(2, len(data), 2)]
    table.setStyle(TableStyle(style))
    return table


def mini_flow_table(steps):
    """A one-row 'box | box | box' flow: steps are (label, sub-label) pairs."""
    cells = [
        Paragraph(f'<b>{label}</b><br/><font size="8.3" color="#4B5D7A">{sub}</font>', S_TABLE_CELL)
        for label, sub in steps
    ]
    table = Table([cells], colWidths=[CONTENT_W / len(steps)] * len(steps))
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BOX_BG),
        ("BOX", (0, 0), (-1, -1), 0.75, BOX_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.75, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def section(number, title, *blocks):
    """A numbered H1 kept together with its first block so a heading never ends a page alone."""
    heading = Paragraph(f"{number}. {title}" if number is not None else title, S_H1)
    if not blocks:
        return [heading]
    return [KeepTogether([heading, blocks[0]]), *blocks[1:]]


def toc_table(entries):
    head = ParagraphStyle("TocHead", parent=S_TOC_ITEM, textColor=colors.white, fontName="Helvetica-Bold")
    rows = [[Paragraph("#", head), Paragraph("Contents", head)]]
    rows += [[Paragraph(str(n), S_TOC_ITEM), Paragraph(t, S_TOC_ITEM)] for n, t in entries]
    table = Table(rows, colWidths=[0.45 * inch, CONTENT_W - 0.45 * inch])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.5, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]
    style += [("BACKGROUND", (0, i), (-1, i), ROW_ALT) for i in range(1, len(rows), 2)]
    table.setStyle(TableStyle(style))
    return table


def build_pdf(filename, footer_label, title, subtitle, tagline, version_line, intro_lines, body):
    def on_page(canvas, doc):
        canvas.setStrokeColor(GRID)
        canvas.setLineWidth(0.6)
        canvas.line(MARGIN, 0.6 * inch, PAGE_W - MARGIN, 0.6 * inch)
        canvas.setFont("Helvetica", 8.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN, 0.42 * inch, footer_label)
        canvas.drawRightString(PAGE_W - MARGIN, 0.42 * inch, f"Page {doc.page}")

    doc = SimpleDocTemplate(
        str(filename), pagesize=letter, title=title,
        leftMargin=MARGIN, rightMargin=MARGIN, topMargin=1.1 * inch, bottomMargin=0.9 * inch,
    )
    story = [Spacer(1, 1.7 * inch), Paragraph(title, S_TITLE), Paragraph(subtitle, S_SUBTITLE)]
    if tagline:
        story.append(Paragraph(tagline, S_TAGLINE))
    story += [Paragraph(version_line, S_VERSION), Spacer(1, 14),
              HRFlowable(width="100%", thickness=1.2, color=NAVY, spaceAfter=14)]
    story += [Paragraph(line, S_INTRO) for line in intro_lines]
    story += body
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"wrote {filename}")


__all__ = [
    "DOCS_DIR", "CONTENT_W", "MARGIN", "PAGE_W", "inch", "PageBreak", "Spacer", "Paragraph",
    "KeepTogether", "S_H1", "S_CENTER_NOTE", "S_FOOTNOTE",
    "bullets", "para", "h2", "callout", "data_table", "mini_flow_table", "section", "toc_table",
    "build_pdf",
]
