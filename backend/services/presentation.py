from __future__ import annotations

import hashlib
import io
import math
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import pymupdf as fitz
from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_TICK_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from services.export_coverage import check_coverage, coverage_failure_message
from services.presentation_model import PresentationModel, build_presentation_model


class ExportValidationError(RuntimeError):
    pass



INK = RGBColor(0x1E, 0x29, 0x3B)
MUTED = RGBColor(0x64, 0x74, 0x8B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
PAGE_BG = RGBColor(0xFF, 0xFF, 0xFF)
TITLE_BG = RGBColor(0x2E, 0x1F, 0x66)
TITLE_BG_ACCENT = RGBColor(0x6D, 0x28, 0xD9)
RISK_RED = RGBColor(0xEF, 0x44, 0x44)

ACCENTS = [
    RGBColor(0x63, 0x66, 0xF1), RGBColor(0xEC, 0x48, 0x99), RGBColor(0xF5, 0x9E, 0x0B),
    RGBColor(0x10, 0xB9, 0x81), RGBColor(0x3B, 0x82, 0xF6), RGBColor(0x8B, 0x5C, 0xF6),
]

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
MARGIN = Inches(0.55)
FONT = "Calibri"


def _accent(index: int) -> RGBColor:
    return ACCENTS[index % len(ACCENTS)]


def _blank_slide(prs: Presentation):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    bg.fill.solid()
    bg.fill.fore_color.rgb = PAGE_BG
    bg.line.fill.background()
    bg.shadow.inherit = False
    slide.shapes._spTree.remove(bg._element)
    slide.shapes._spTree.insert(2, bg._element)
    return slide


def _textbox(slide, x, y, w, h, text, size=14, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, wrap=True):
    box = slide.shapes.add_textbox(x, y, w, h)
    frame = box.text_frame
    frame.word_wrap = wrap
    frame.vertical_anchor = anchor
    for i, line in enumerate(str(text).split("\n")):
        paragraph = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        paragraph.alignment = align
        run = paragraph.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.name = FONT
        run.font.color.rgb = color
    return box


def _bullets(slide, x, y, w, h, items, size=14, color=INK, bullet_color=None, spacing=6):
    box = slide.shapes.add_textbox(x, y, w, h)
    frame = box.text_frame
    frame.word_wrap = True
    for i, item in enumerate(items):
        paragraph = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        paragraph.space_after = Pt(spacing)
        marker = paragraph.add_run()
        marker.text = "●  "
        marker.font.size = Pt(size)
        marker.font.name = FONT
        marker.font.color.rgb = bullet_color or color
        text_run = paragraph.add_run()
        text_run.text = str(item)
        text_run.font.size = Pt(size)
        text_run.font.name = FONT
        text_run.font.color.rgb = color
    return box


def _header_bar(slide, title: str, accent: RGBColor, subtitle: str = ""):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, Inches(1.05))
    bar.fill.solid()
    bar.fill.fore_color.rgb = accent
    bar.line.fill.background()
    bar.shadow.inherit = False
    _textbox(slide, MARGIN, Inches(0.16), SLIDE_W - 2 * MARGIN, Inches(0.55), title.upper(), size=24, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    if subtitle:
        _textbox(slide, MARGIN, Inches(0.62), SLIDE_W - 2 * MARGIN, Inches(0.35), subtitle, size=12, color=WHITE)


def _footer(slide, source_refs: list[dict]):
    if not source_refs:
        return
    seen, lines = set(), []
    for ref in source_refs[:4]:
        key = (ref.get("document"), ref.get("page"))
        if key in seen:
            continue
        seen.add(key)
        page = f" p.{ref['page']}" if ref.get("page") is not None else ""
        lines.append(f"{ref.get('document', 'Uploaded report')}{page}")
    _textbox(slide, MARGIN, SLIDE_H - Inches(0.5), SLIDE_W - 2 * MARGIN, Inches(0.4),
             "Source: " + " | ".join(lines), size=9, color=MUTED)


def _page_number(slide, n: int):
    _textbox(slide, SLIDE_W - Inches(0.9), SLIDE_H - Inches(0.5), Inches(0.6), Inches(0.4), str(n), size=9, color=MUTED, align=PP_ALIGN.RIGHT)





def _title_slide(prs, section, currency):
    slide = _blank_slide(prs)
    band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    band.fill.solid()
    band.fill.fore_color.rgb = TITLE_BG
    band.line.fill.background()
    band.shadow.inherit = False
    accent = slide.shapes.add_shape(MSO_SHAPE.OVAL, SLIDE_W - Inches(4.2), -Inches(1.6), Inches(5.5), Inches(5.5))
    accent.fill.solid()
    accent.fill.fore_color.rgb = TITLE_BG_ACCENT
    accent.line.fill.background()
    accent.shadow.inherit = False
    _textbox(slide, Inches(0.7), Inches(2.9), Inches(10), Inches(1.3), section.title, size=40, color=WHITE, bold=True)
    _textbox(slide, Inches(0.7), Inches(3.9), Inches(10), Inches(0.6), "FINANCIAL INTELLIGENCE REPORT", size=18, color=ACCENTS[2], bold=True)
    if section.body.get("period"):
        _textbox(slide, Inches(0.7), Inches(4.75), Inches(10), Inches(0.5), section.body["period"], size=14, color=RGBColor(0xC7, 0xC1, 0xE8))
    _textbox(slide, Inches(0.7), SLIDE_H - Inches(0.9), Inches(11), Inches(0.5),
             "Every figure traces to a page-level source reference.", size=11, color=RGBColor(0xC7, 0xC1, 0xE8))
    return slide


def _summary_slide(prs, section, idx):
    slide = _blank_slide(prs)
    _header_bar(slide, section.title, ACCENTS[1])
    paragraphs = [p for p in section.body.get("paragraphs", []) if isinstance(p, str)]
    _textbox(slide, MARGIN, Inches(1.4), SLIDE_W - 2 * MARGIN, SLIDE_H - Inches(2.1),
             "\n\n".join(paragraphs), size=15, color=INK)
    _footer(slide, section.source_refs)
    _page_number(slide, idx)
    return slide


def _documents_slide(prs, section, idx):
    slide = _blank_slide(prs)
    _header_bar(slide, section.title, ACCENTS[4])
    reports = section.body.get("reports", [])
    _textbox(slide, MARGIN, Inches(1.35), SLIDE_W - 2 * MARGIN, Inches(0.5),
             f"Documents analyzed: {len(reports)}", size=16, color=INK, bold=True)
    lines = []
    for r in reports:
        period = r.get("period")
        prefix = f"{period} - " if period and period != "Undated report" else ""
        doc_type = f"  ({r.get('documentType')})" if r.get("documentType") else ""
        lines.append(f"{prefix}{r.get('filename', 'Uploaded report')}{doc_type}")
    _bullets(slide, MARGIN, Inches(2.0), SLIDE_W - 2 * MARGIN, Inches(3.6), lines, size=14, bullet_color=ACCENTS[4])
    if section.body.get("period"):
        _textbox(slide, MARGIN, SLIDE_H - Inches(1.1), SLIDE_W - 2 * MARGIN, Inches(0.5),
                 f"Reporting period: {section.body['period']}", size=12, color=MUTED)
    _page_number(slide, idx)
    return slide


def _kpi_slide(prs, section, idx):
    slide = _blank_slide(prs)
    _header_bar(slide, section.title, ACCENTS[0])
    metrics = section.body.get("metrics", [])
    currency = section.body.get("currency", "")
    cols = min(3, len(metrics)) or 1
    gap = Inches(0.3)
    card_w = (SLIDE_W - 2 * MARGIN - gap * (cols - 1)) / cols
    card_h = Inches(1.9)
    top = Inches(1.5)
    for i, metric in enumerate(metrics):
        row, col = divmod(i, cols)
        x = MARGIN + col * (card_w + gap)
        y = top + row * (card_h + gap)
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, card_w, card_h)
        card.adjustments[0] = 0.08
        card.fill.solid()
        card.fill.fore_color.rgb = _accent(i)
        card.line.fill.background()
        card.shadow.inherit = False
        _textbox(slide, x + Inches(0.2), y + Inches(0.18), card_w - Inches(0.4), Inches(0.4),
                 str(metric.get("label", metric.get("field", ""))).upper(), size=13, color=WHITE, bold=True)
        value = metric.get("value")
        text = _money(value, currency) if isinstance(value, (int, float)) else str(value)
        _textbox(slide, x + Inches(0.2), y + Inches(0.65), card_w - Inches(0.4), Inches(1.0), text,
                 size=24, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        if metric.get("status") in {"conflicting", "needs_review"}:
            _textbox(slide, x + Inches(0.2), y + card_h - Inches(0.42), card_w - Inches(0.4), Inches(0.35),
                     metric["status"].replace("_", " ").title(), size=10, color=WHITE)
    _footer(slide, section.source_refs)
    _page_number(slide, idx)
    return slide


def _line_chart_slide(prs, section, idx):
    slide = _blank_slide(prs)
    _header_bar(slide, section.title, ACCENTS[3])
    series = section.body.get("series", [])
    chart_data = CategoryChartData()
    chart_data.categories = [str(p.get("period", "")) for p in series]
    chart_data.add_series(section.body.get("unit") or "Value", tuple(p.get("value", 0) for p in series))
    frame = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, MARGIN, Inches(1.5), SLIDE_W - 2 * MARGIN, Inches(4.8), chart_data)
    chart = frame.chart
    chart.has_title = False
    chart.has_legend = False
    plot = chart.plots[0]
    plot.has_data_labels = True
    plot.data_labels.number_format = "#,##0"
    plot.data_labels.number_format_is_linked = False
    plot.data_labels.font.size = Pt(10)
    chart.series[0].format.line.color.rgb = ACCENTS[3]
    chart.category_axis.tick_labels.font.size = Pt(11)
    chart.value_axis.tick_labels.font.size = Pt(10)
    _footer(slide, section.source_refs)
    _page_number(slide, idx)
    return slide


def _breakdown_rows(rows, limit=8):
    rows = [
        {"category": str(r.get("category", "")), "amount": r["amount"]}
        for r in rows
        if isinstance(r, dict) and isinstance(r.get("amount"), (int, float)) and not isinstance(r.get("amount"), bool) and r["amount"] != 0
    ]
    if len(rows) <= limit:
        return rows
    rows = sorted(rows, key=lambda r: abs(r["amount"]), reverse=True)
    return rows[:limit - 1] + [{"category": "Other", "amount": sum(r["amount"] for r in rows[limit - 1:])}]


def _can_use_pie(rows) -> bool:
    return len(rows) >= 2 and all(r["amount"] > 0 for r in rows)


def _keep_negative_bars(series):
    series.invert_if_negative = False
    for point in series._element.findall(qn("c:dPt")):
        if point.find(qn("c:invertIfNegative")) is None:
            point.find(qn("c:idx")).addnext(etree.Element(qn("c:invertIfNegative"), val="0"))


def _pie_slide(prs, section, idx):
    slide = _blank_slide(prs)
    _header_bar(slide, section.title, ACCENTS[4])
    breakdowns = section.body.get("breakdowns", [])
    currency = section.body.get("currency", "")
    n = max(len(breakdowns), 1)
    chart_w = (SLIDE_W - 2 * MARGIN) / n
    for i, bd in enumerate(breakdowns):
        rows = _breakdown_rows(bd.get("rows", []))
        x = MARGIN + i * chart_w
        _textbox(slide, x, Inches(1.25), chart_w - Inches(0.2), Inches(0.4), str(bd.get("subtitle", "")).upper(), size=13, color=MUTED, bold=True)
        if not rows:
            continue
        chart_data = CategoryChartData()
        chart_data.categories = [r["category"] for r in rows]
        chart_data.add_series(bd.get("subtitle", ""), tuple(r["amount"] for r in rows))
        if _can_use_pie(rows):
            frame = slide.shapes.add_chart(XL_CHART_TYPE.PIE, x, Inches(1.7), chart_w - Inches(0.3), Inches(4.6), chart_data)
            chart = frame.chart
            chart.has_legend = True
            chart.legend.position = XL_LEGEND_POSITION.BOTTOM
            chart.legend.include_in_layout = False
            chart.legend.font.size = Pt(10)
        else:
            frame = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, x, Inches(1.7), chart_w - Inches(0.3), Inches(4.6), chart_data)
            chart = frame.chart
            chart.has_legend = False
            chart.category_axis.reverse_order = True
            chart.category_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW
            chart.category_axis.tick_labels.font.size = Pt(9)
            chart.value_axis.tick_labels.font.size = Pt(9)
            chart.value_axis.tick_labels.number_format = "#,##0"
            chart.value_axis.tick_labels.number_format_is_linked = False
        chart.has_title = False
        plot = chart.plots[0]
        plot.has_data_labels = True
        plot.data_labels.number_format = "#,##0"
        plot.data_labels.number_format_is_linked = False
        plot.data_labels.font.size = Pt(9)
        for j, point in enumerate(plot.series[0].points):
            point.format.fill.solid()
            point.format.fill.fore_color.rgb = _accent(j) if _can_use_pie(rows) else (RISK_RED if rows[j]["amount"] < 0 else ACCENTS[4])
        if not _can_use_pie(rows):
            _keep_negative_bars(plot.series[0])
    _footer(slide, section.source_refs)
    _page_number(slide, idx)
    return slide


def _ratio_slide(prs, section, idx):
    slide = _blank_slide(prs)
    _header_bar(slide, section.title, ACCENTS[0])
    rows = section.body.get("rows", [])
    per_slide = 12
    _rows_block(slide, rows[:per_slide])
    _footer(slide, section.source_refs)
    _page_number(slide, idx)
    return slide


def _rows_block(slide, rows):
    top = Inches(1.45)
    row_h = Inches(0.46)
    for i, row in enumerate(rows):
        y = top + i * row_h
        stripe = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, MARGIN, y, Inches(0.08), row_h - Inches(0.1))
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = _accent(i)
        stripe.line.fill.background()
        stripe.shadow.inherit = False
        _textbox(slide, MARGIN + Inches(0.25), y, Inches(8.5), row_h, str(row.get("ratio", "")), size=13, color=INK)
        value = row.get("value")
        text = f"{value}{'%' if row.get('isPercentage') else ''}" if value is not None else ""
        _textbox(slide, SLIDE_W - MARGIN - Inches(2.6), y, Inches(2.4), row_h, text, size=13, color=ACCENTS[0], bold=True, align=PP_ALIGN.RIGHT)


def _table_slide(prs, section, idx, *, columns=None, rows=None, title=None):
    columns = columns or section.body.get("columns", [])
    rows = rows if rows is not None else section.body.get("rows", [])
    slide = _blank_slide(prs)
    _header_bar(slide, title or section.title, ACCENTS[5])
    if not columns:
        _textbox(slide, MARGIN, Inches(1.5), SLIDE_W - 2 * MARGIN, Inches(1), "No data", size=14, color=MUTED)
        _page_number(slide, idx)
        return slide
    n_rows = len(rows) + 1
    table_shape = slide.shapes.add_table(n_rows, len(columns), MARGIN, Inches(1.4),
                                         SLIDE_W - 2 * MARGIN, Inches(min(5.4, 0.42 * n_rows + 0.4))).table
    for c, name in enumerate(columns):
        cell = table_shape.cell(0, c)
        cell.text = str(name)
        cell.text_frame.paragraphs[0].runs[0].font.size = Pt(11)
        cell.text_frame.paragraphs[0].runs[0].font.bold = True
        cell.text_frame.paragraphs[0].runs[0].font.color.rgb = WHITE
        cell.fill.solid()
        cell.fill.fore_color.rgb = ACCENTS[5]
    for r, row in enumerate(rows, start=1):
        for c in range(len(columns)):
            cell = table_shape.cell(r, c)
            cell.text = str(row[c]) if c < len(row) else ""
            run = cell.text_frame.paragraphs[0].runs[0] if cell.text_frame.paragraphs[0].runs else cell.text_frame.paragraphs[0].add_run()
            run.font.size = Pt(10)
            run.font.color.rgb = INK
    _footer(slide, section.source_refs)
    _page_number(slide, idx)
    return slide


def _narrative_slide(prs, section, idx):
    slide = _blank_slide(prs)
    accent = RISK_RED if section.body.get("accent") == "risk" else ACCENTS[2]
    _header_bar(slide, section.title, accent)
    bullets = [str(b) for b in section.body.get("bullets", []) if b][:12]
    _bullets(slide, MARGIN, Inches(1.4), SLIDE_W - 2 * MARGIN, SLIDE_H - Inches(2.1), bullets, size=15, color=INK, bullet_color=accent)
    _footer(slide, section.source_refs)
    _page_number(slide, idx)
    return slide


def _notes_slide(prs, section, idx):
    slide = _blank_slide(prs)
    _header_bar(slide, section.title, ACCENTS[0])
    y = Inches(1.35)
    for note in section.body.get("notes", []):
        _textbox(slide, MARGIN, y, SLIDE_W - 2 * MARGIN, Inches(0.4), note.get("category", "").upper(), size=13, color=ACCENTS[0], bold=True)
        y += Inches(0.42)
        items = [str(i) for i in note.get("items", [])][:5]
        _bullets(slide, MARGIN + Inches(0.15), y, SLIDE_W - 2 * MARGIN - Inches(0.15), Inches(0.34 * len(items) + 0.1), items, size=12)
        y += Inches(0.34 * len(items) + 0.25)
    _footer(slide, section.source_refs)
    _page_number(slide, idx)
    return slide


def _data_status_slide(prs, section, idx):
    slide = _blank_slide(prs)
    _header_bar(slide, section.title, RISK_RED)
    y = Inches(1.4)
    conflicts = section.body.get("conflicts", [])
    if conflicts:
        _textbox(slide, MARGIN, y, SLIDE_W - 2 * MARGIN, Inches(0.4), "SOURCE CONFLICTS", size=13, color=RISK_RED, bold=True)
        y += Inches(0.45)
        lines = [f"{c.get('field')}: sources disagree by ~{c.get('spreadPercent')}% for the same period (shown unresolved)" for c in conflicts]
        _bullets(slide, MARGIN + Inches(0.15), y, SLIDE_W - 2 * MARGIN, Inches(0.34 * len(lines) + 0.1), lines, size=12, bullet_color=RISK_RED)
        y += Inches(0.34 * len(lines) + 0.35)
    missing = section.body.get("missing", [])
    if missing:
        _textbox(slide, MARGIN, y, SLIDE_W - 2 * MARGIN, Inches(0.4), "NOT IDENTIFIED IN THE VERIFIED SOURCES", size=13, color=MUTED, bold=True)
        y += Inches(0.45)
        _bullets(slide, MARGIN + Inches(0.15), y, SLIDE_W - 2 * MARGIN, Inches(0.34 * len(missing) + 0.1),
                 [m.get("message", m.get("label", "")) for m in missing], size=12, color=MUTED)
    _page_number(slide, idx)
    return slide


def _sources_slide(prs, section, idx):
    slide = _blank_slide(prs)
    _header_bar(slide, section.title, ACCENTS[4])
    lines = []
    for r in section.body.get("reports", []):
        period = f" - {r.get('period')}" if r.get("period") and r.get("period") != "Undated report" else ""
        doc_type = f" ({r.get('documentType')})" if r.get("documentType") else ""
        lines.append(f"{r.get('filename', 'Uploaded report')}{period}{doc_type}")
    _bullets(slide, MARGIN, Inches(1.45), SLIDE_W - 2 * MARGIN, Inches(3.6), lines, size=14, bullet_color=ACCENTS[4])
    external = section.body.get("external", {})
    if external.get("message"):
        _textbox(slide, MARGIN, SLIDE_H - Inches(1.0), SLIDE_W - 2 * MARGIN, Inches(0.5), external["message"], size=10, color=MUTED)
    _page_number(slide, idx)
    return slide


_KIND_BUILDERS = {
    "summary": _summary_slide,
    "documents": _documents_slide,
    "kpi": _kpi_slide,
    "line_chart": _line_chart_slide,
    "pie": _pie_slide,
    "ratios": _ratio_slide,
    "table": _table_slide,
    "narrative": _narrative_slide,
    "notes": _notes_slide,
    "data_status": _data_status_slide,
    "sources": _sources_slide,
}


def _money(value, currency: str) -> str:
    if not isinstance(value, (int, float)):
        return str(value)
    a = abs(value)
    for scale, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if a >= scale:
            return f"{currency} {value / scale:,.2f}{suffix}".strip()
    return f"{currency} {value:,.0f}".strip()





def build_pptx(data: dict, model: PresentationModel | None = None) -> bytes:
    model = model or build_presentation_model(data)

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    for idx, section in enumerate(model.sections, start=1):
        if section.kind == "title":
            _title_slide(prs, section, model.currency)
            continue
        builder = _KIND_BUILDERS.get(section.kind)
        if builder is None:
            continue

        if section.kind == "table" and len(section.body.get("rows", [])) > 14:
            rows = section.body["rows"]
            for part, start in enumerate(range(0, len(rows), 14)):
                _table_slide(prs, section, idx, columns=section.body["columns"], rows=rows[start:start + 14],
                             title=f"{section.title} ({part + 1})" if len(rows) > 14 else section.title)
        else:
            builder(prs, section, idx)

    buffer = tempfile.NamedTemporaryFile(suffix=".pptx", delete=False)
    path = Path(buffer.name)
    buffer.close()
    try:
        prs.save(str(path))
        return path.read_bytes()
    finally:
        path.unlink(missing_ok=True)




_REQUIRED_OPC_PARTS = ("[Content_Types].xml", "_rels/.rels", "ppt/presentation.xml", "ppt/_rels/presentation.xml.rels")


def _validate_opc_package(pptx_bytes: bytes) -> int:

    try:
        archive = zipfile.ZipFile(io.BytesIO(pptx_bytes))
    except zipfile.BadZipFile as exc:
        raise ExportValidationError(f"Generated PPTX is not a valid zip: {exc}") from exc
    if archive.testzip() is not None:
        raise ExportValidationError("Generated PPTX zip has a corrupt member")
    names = set(archive.namelist())
    missing = [p for p in _REQUIRED_OPC_PARTS if p not in names]
    if missing:
        raise ExportValidationError(f"Generated PPTX is missing required package parts: {', '.join(missing)}")

    slide_parts = sorted(n for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml"))
    if not slide_parts:
        raise ExportValidationError("Generated PPTX contains no slide parts")
    for part in slide_parts:
        try:
            ElementTree.fromstring(archive.read(part))
        except ElementTree.ParseError as exc:
            raise ExportValidationError(f"Slide part {part} is not well-formed XML: {exc}") from exc
        rels = f"ppt/slides/_rels/{part.split('/')[-1]}.rels"
        if rels not in names:
            raise ExportValidationError(f"Slide part {part} has no relationships part")

    try:
        pres_xml = ElementTree.fromstring(archive.read("ppt/presentation.xml"))
    except ElementTree.ParseError as exc:
        raise ExportValidationError(f"ppt/presentation.xml is not well-formed: {exc}") from exc
    ns = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
    listed = pres_xml.findall(".//p:sldIdLst/p:sldId", ns)
    if len(listed) != len(slide_parts):
        raise ExportValidationError(
            f"presentation.xml lists {len(listed)} slides but the package has {len(slide_parts)} slide parts"
        )
    return len(slide_parts)


def validate_pptx(pptx_bytes: bytes) -> int:

    opc_slides = _validate_opc_package(pptx_bytes)

    try:
        prs = Presentation(io.BytesIO(pptx_bytes))
    except Exception as exc:
        raise ExportValidationError(f"Generated PPTX could not be opened: {exc}") from exc

    slide_count = len(prs.slides)
    if slide_count == 0:
        raise ExportValidationError("Generated PPTX has no slides")
    if slide_count != opc_slides:
        raise ExportValidationError(f"python-pptx sees {slide_count} slides, package has {opc_slides}")

    for index, slide in enumerate(prs.slides, start=1):
        has_content = any(
            (getattr(shape, "has_chart", False) and shape.has_chart)
            or (getattr(shape, "has_table", False) and shape.has_table)
            or (getattr(shape, "has_text_frame", False) and shape.text_frame.text.strip())
            for shape in slide.shapes
        )
        if not has_content:
            raise ExportValidationError(f"Slide {index} has no readable content")

    return slide_count


def enforce_coverage(data: dict, model: PresentationModel) -> dict:

    from services.logging_config import get_logger

    coverage = check_coverage(data, model)
    structural_gap = bool(coverage["missingCharts"] or coverage["missingTables"] or len(coverage["missingKeys"]) > 2)
    if structural_gap:
        raise ExportValidationError(coverage_failure_message(coverage))
    if coverage["missingKeys"]:
        get_logger(__name__).warning(
            "export_coverage_incomplete", extra={"missing": coverage["missingKeys"]}
        )
    return coverage





def pdf_export(pptx_bytes: bytes, data: dict | None = None, model: PresentationModel | None = None) -> tuple[bytes, str]:

    try:
        return _pdf_via_soffice(pptx_bytes), "soffice"
    except (OSError, subprocess.SubprocessError, RuntimeError) as primary_exc:
        if data is None and model is None:
            raise RuntimeError(f"PDF export is unavailable on this server: {primary_exc}") from primary_exc
        try:
            return _pdf_via_pymupdf(model or build_presentation_model(data)), "fallback"
        except Exception as fallback_exc:
            raise RuntimeError(
                f"PDF export failed on both paths (primary: {primary_exc}; fallback: {fallback_exc})"
            ) from fallback_exc


def _pdf_via_soffice(pptx_bytes: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as directory:
        pptx = Path(directory) / "company-intelligence.pptx"
        pptx.write_bytes(pptx_bytes)
        subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf", "--outdir", directory, str(pptx)],
            check=True, capture_output=True, timeout=60,
        )
        pdf = pptx.with_suffix(".pdf")
        if not pdf.exists():
            raise RuntimeError("LibreOffice did not produce a PDF file")
        return pdf.read_bytes()


_PDF_W, _PDF_H = 960, 540
_PDF_MARGIN = 39.6
_PDF_HEADER_H = 75.6
_PDF_BOTTOM = _PDF_H - 50
_PDF_LIGHT = RGBColor(0xC7, 0xC1, 0xE8)
_PDF_GRID = RGBColor(0xE2, 0xE8, 0xF0)
_PDF_STRIPE = RGBColor(0xF8, 0xFA, 0xFC)

_PDF_REPLACEMENTS = {
    "‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "−": "-",
    "•": "-", "●": "-", "…": "...", "€": "EUR ", "₹": "INR ", " ": " ",
}


def _pdf_clean(text) -> str:
    text = str(text)
    for old, new in _PDF_REPLACEMENTS.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")


def _pdf_color(color) -> tuple:
    return tuple(v / 255 for v in color)


def _pdf_font(bold: bool) -> str:
    return "hebo" if bold else "helv"


def _pdf_width(text: str, size: float, bold: bool = False) -> float:
    return fitz.get_text_length(text, fontname=_pdf_font(bold), fontsize=size)


def _pdf_wrap(text, width: float, size: float, bold: bool = False) -> list[str]:
    lines = []
    for paragraph in _pdf_clean(text).split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}".strip()
            if _pdf_width(candidate, size, bold) <= width:
                line = candidate
                continue
            if line:
                lines.append(line)
            while len(word) > 1 and _pdf_width(word, size, bold) > width:
                cut = len(word) - 1
                while cut > 1 and _pdf_width(word[:cut], size, bold) > width:
                    cut -= 1
                lines.append(word[:cut])
                word = word[cut:]
            line = word
        lines.append(line)
    return lines


def _pdf_text(page, x, y, width, text, size=14, color=INK, bold=False, align="left", max_height=None, min_size=8, leading=1.25):
    lines = _pdf_wrap(text, width, size, bold)
    if max_height is not None:
        while size > min_size and len(lines) * size * leading > max_height:
            size -= 1
            lines = _pdf_wrap(text, width, size, bold)
        max_lines = max(int(max_height // (size * leading)), 1)
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = lines[-1].rstrip(" .,") + "..."
    for line in lines:
        offset = 0
        if align != "left":
            free = width - _pdf_width(line, size, bold)
            offset = free if align == "right" else free / 2
        page.insert_text((x + offset, y + size), line, fontsize=size, fontname=_pdf_font(bold), color=_pdf_color(color))
        y += size * leading
    return y


def _pdf_bullets(page, x, y, width, items, size=14, color=INK, bullet_color=None, max_y=_PDF_BOTTOM, spacing=6):
    items = [str(i) for i in items if str(i).strip()]

    def needed(s):
        return sum(len(_pdf_wrap(i, width - 18, s)) * s * 1.25 + spacing for i in items)

    while size > 9 and y + needed(size) > max_y:
        size -= 1
    for item in items:
        if y + size > max_y:
            break
        page.draw_circle((x + 4, y + size * 0.62), size * 0.2, color=None, fill=_pdf_color(bullet_color or color))
        y = _pdf_text(page, x + 18, y, width - 18, item, size=size, color=color, max_height=max_y - y)
        y += spacing
    return y


def _pdf_page(doc, title: str, accent: RGBColor):
    page = doc.new_page(width=_PDF_W, height=_PDF_H)
    page.draw_rect(fitz.Rect(0, 0, _PDF_W, _PDF_HEADER_H), color=None, fill=_pdf_color(accent))
    text = _pdf_clean(title.upper())
    size = 24
    while size > 14 and _pdf_width(text, size, True) > _PDF_W - 2 * _PDF_MARGIN:
        size -= 1
    page.insert_text((_PDF_MARGIN, _PDF_HEADER_H / 2 + size * 0.35), text, fontsize=size, fontname="hebo", color=(1, 1, 1))
    return page


def _pdf_footer(page, source_refs: list[dict], number: int):
    if source_refs:
        seen, lines = set(), []
        for ref in source_refs[:4]:
            key = (ref.get("document"), ref.get("page"))
            if key in seen:
                continue
            seen.add(key)
            page_text = f" p.{ref['page']}" if ref.get("page") is not None else ""
            lines.append(f"{ref.get('document', 'Uploaded report')}{page_text}")
        _pdf_text(page, _PDF_MARGIN, _PDF_H - 36, _PDF_W - 2 * _PDF_MARGIN - 60, "Source: " + " | ".join(lines),
                  size=9, color=MUTED, max_height=24)
    _pdf_text(page, _PDF_W - 64.8, _PDF_H - 36, 43.2, str(number), size=9, color=MUTED, align="right")


def _pdf_title(doc, section, idx):
    page = doc.new_page(width=_PDF_W, height=_PDF_H)
    page.draw_rect(fitz.Rect(0, 0, _PDF_W, _PDF_H), color=None, fill=_pdf_color(TITLE_BG))
    page.draw_circle((855.6, 82.8), 198, color=None, fill=_pdf_color(TITLE_BG_ACCENT))
    _pdf_text(page, 50.4, 200, 720, section.title, size=40, color=WHITE, bold=True, max_height=80, min_size=24)
    _pdf_text(page, 50.4, 284, 720, "FINANCIAL INTELLIGENCE REPORT", size=18, color=ACCENTS[2], bold=True)
    if section.body.get("period"):
        _pdf_text(page, 50.4, 342, 720, section.body["period"], size=14, color=_PDF_LIGHT)
    _pdf_text(page, 50.4, _PDF_H - 64.8, 792, "Every figure traces to a page-level source reference.", size=11, color=_PDF_LIGHT)


def _pdf_summary(doc, section, idx):
    page = _pdf_page(doc, section.title, ACCENTS[1])
    paragraphs = [p for p in section.body.get("paragraphs", []) if isinstance(p, str)]
    _pdf_text(page, _PDF_MARGIN, 100.8, _PDF_W - 2 * _PDF_MARGIN, "\n\n".join(paragraphs), size=15, max_height=388.8)
    _pdf_footer(page, section.source_refs, idx)


def _pdf_documents(doc, section, idx):
    page = _pdf_page(doc, section.title, ACCENTS[4])
    reports = section.body.get("reports", [])
    _pdf_text(page, _PDF_MARGIN, 97.2, _PDF_W - 2 * _PDF_MARGIN, f"Documents analyzed: {len(reports)}", size=16, bold=True)
    lines = []
    for r in reports:
        period = r.get("period")
        prefix = f"{period} - " if period and period != "Undated report" else ""
        doc_type = f"  ({r.get('documentType')})" if r.get("documentType") else ""
        lines.append(f"{prefix}{r.get('filename', 'Uploaded report')}{doc_type}")
    _pdf_bullets(page, _PDF_MARGIN, 144, _PDF_W - 2 * _PDF_MARGIN, lines, size=14, bullet_color=ACCENTS[4], max_y=403.2)
    if section.body.get("period"):
        _pdf_text(page, _PDF_MARGIN, _PDF_H - 79.2, _PDF_W - 2 * _PDF_MARGIN, f"Reporting period: {section.body['period']}", size=12, color=MUTED)
    _pdf_footer(page, [], idx)


def _pdf_kpi(doc, section, idx):
    page = _pdf_page(doc, section.title, ACCENTS[0])
    metrics = section.body.get("metrics", [])
    currency = section.body.get("currency", "")
    cols = min(3, len(metrics)) or 1
    gap = 21.6
    card_w = (_PDF_W - 2 * _PDF_MARGIN - gap * (cols - 1)) / cols
    card_h = 136.8
    for i, metric in enumerate(metrics[:6]):
        row, col = divmod(i, cols)
        x = _PDF_MARGIN + col * (card_w + gap)
        y = 108 + row * (card_h + gap)
        page.draw_rect(fitz.Rect(x, y, x + card_w, y + card_h), color=None, fill=_pdf_color(_accent(i)), radius=0.08)
        _pdf_text(page, x + 14.4, y + 14, card_w - 28.8, str(metric.get("label", metric.get("field", ""))).upper(),
                  size=13, color=WHITE, bold=True, max_height=34)
        value = metric.get("value")
        text = _money(value, currency) if isinstance(value, (int, float)) else str(value)
        _pdf_text(page, x + 14.4, y + 58, card_w - 28.8, text, size=24, color=WHITE, bold=True, max_height=56, min_size=14)
        if metric.get("status") in {"conflicting", "needs_review"}:
            _pdf_text(page, x + 14.4, y + card_h - 26, card_w - 28.8, metric["status"].replace("_", " ").title(), size=10, color=WHITE)
    _pdf_footer(page, section.source_refs, idx)


def _pdf_axis_values(low: float, high: float, steps: int = 5) -> list[float]:
    if low == high:
        high = low + (abs(low) or 1)
    raw = (high - low) / steps
    magnitude = 10 ** math.floor(math.log10(raw))
    step = next(m * magnitude for m in (1, 2, 2.5, 5, 10) if m * magnitude >= raw)
    start = math.floor(low / step) * step
    end = math.ceil(high / step) * step
    return [start + step * i for i in range(int(round((end - start) / step)) + 1)]


def _pdf_line_chart(doc, section, idx):
    page = _pdf_page(doc, section.title, ACCENTS[3])
    series = [p for p in section.body.get("series", []) if isinstance(p.get("value"), (int, float))]
    currency = section.body.get("currency", "")
    left, top, right, bottom = _PDF_MARGIN + 80, 120, _PDF_W - _PDF_MARGIN - 20, 410
    values = [p["value"] for p in series] or [0]
    ticks = _pdf_axis_values(min(0, min(values)), max(0, max(values)))
    low, high = ticks[0], ticks[-1]

    def y_of(v):
        return bottom - (v - low) / (high - low) * (bottom - top)

    for tick in ticks:
        y = y_of(tick)
        page.draw_line((left, y), (right, y), color=_pdf_color(_PDF_GRID), width=0.8)
        _pdf_text(page, _PDF_MARGIN, y - 7, 72, _money(tick, ""), size=10, color=MUTED, align="right")
    step = (right - left) / max(len(series), 1)
    points = [(left + step * (i + 0.5), y_of(p["value"])) for i, p in enumerate(series)]
    if len(points) > 1:
        page.draw_polyline(points, color=_pdf_color(ACCENTS[3]), width=2.5)
    for (x, y), p in zip(points, series):
        page.draw_circle((x, y), 4.5, color=_pdf_color(WHITE), fill=_pdf_color(ACCENTS[3]), width=1.5)
        _pdf_text(page, x - step / 2, y - 26, step, _money(p["value"], currency), size=10, bold=True, align="center")
        _pdf_text(page, x - step / 2 + 4, bottom + 10, step - 8, str(p.get("period", "")), size=11, color=MUTED, align="center", max_height=44)
    _pdf_footer(page, section.source_refs, idx)


def _pdf_pie(page, rows, x, y, width, currency):
    total = sum(r["amount"] for r in rows)
    radius = min(width / 2 - 10, 92)
    cx, cy = x + width / 2, y + radius + 6
    start = -90.0
    for j, r in enumerate(rows):
        sweep = r["amount"] / total * 360
        steps = max(int(sweep / 2), 2)
        arc = [(cx + radius * math.cos(math.radians(start + sweep * s / steps)),
                cy + radius * math.sin(math.radians(start + sweep * s / steps))) for s in range(steps + 1)]
        page.draw_polyline([(cx, cy), *arc, (cx, cy)], color=(1, 1, 1), fill=_pdf_color(_accent(j)), width=1.2, closePath=True)
        start += sweep
    legend_y = cy + radius + 18
    row_h = min(20, (_PDF_BOTTOM - legend_y) / max(len(rows), 1))
    size = min(10, row_h * 0.6)
    for j, r in enumerate(rows):
        ly = legend_y + j * row_h
        page.draw_rect(fitz.Rect(x, ly + 2, x + 10, ly + 12), color=None, fill=_pdf_color(_accent(j)))
        value = f"{_money(r['amount'], currency)}  ({r['amount'] / total * 100:.1f}%)"
        value_w = _pdf_width(value, size, True) + 4
        _pdf_text(page, x + 16, ly, width - 16 - value_w, r["category"], size=size, max_height=row_h, min_size=size)
        _pdf_text(page, x + width - value_w, ly, value_w, value, size=size, bold=True, align="right")


def _pdf_bars(page, rows, x, y, width, currency):
    label_w = width * 0.36
    value_w = 74
    low = min(0, min(r["amount"] for r in rows))
    high = max(0, max(r["amount"] for r in rows))
    bar_left = x + label_w + 8 + (value_w if low < 0 else 0)
    bar_right = x + width - (value_w if high > 0 else 0)
    span = (high - low) or 1

    def x_of(v):
        return bar_left + (v - low) / span * (bar_right - bar_left)

    zero = x_of(0)
    row_h = min(34, (_PDF_BOTTOM - y) / len(rows))
    bar_h = row_h * 0.62
    for j, r in enumerate(rows):
        ry = y + j * row_h
        label_lines = min(len(_pdf_wrap(r["category"], label_w, 9)), 2)
        _pdf_text(page, x, ry + (row_h - 9 * 1.25 * label_lines) / 2, label_w, r["category"], size=9, color=INK,
                  max_height=row_h, min_size=7, align="right")
        end = x_of(r["amount"])
        color = RISK_RED if r["amount"] < 0 else ACCENTS[4]
        page.draw_rect(fitz.Rect(min(zero, end), ry + (row_h - bar_h) / 2, max(zero, end), ry + (row_h + bar_h) / 2),
                       color=None, fill=_pdf_color(color))
        label_x = max(zero, end) + 4 if r["amount"] >= 0 else min(zero, end) - value_w - 4
        _pdf_text(page, label_x, ry + row_h / 2 - 6, value_w, _money(r["amount"], currency), size=9, bold=True,
                  align="left" if r["amount"] >= 0 else "right")
    page.draw_line((zero, y), (zero, y + row_h * len(rows)), color=_pdf_color(MUTED), width=0.8)


def _pdf_breakdowns(doc, section, idx):
    page = _pdf_page(doc, section.title, ACCENTS[4])
    breakdowns = section.body.get("breakdowns", [])
    currency = section.body.get("currency", "")
    gap = 36
    n = max(len(breakdowns), 1)
    chart_w = (_PDF_W - 2 * _PDF_MARGIN - gap * (n - 1)) / n
    for i, bd in enumerate(breakdowns):
        x = _PDF_MARGIN + i * (chart_w + gap)
        _pdf_text(page, x, 90, chart_w, str(bd.get("subtitle", "")).upper(), size=13, color=MUTED, bold=True)
        rows = _breakdown_rows(bd.get("rows", []))
        if not rows:
            continue
        if _can_use_pie(rows):
            _pdf_pie(page, rows, x, 120, chart_w, currency)
        else:
            _pdf_bars(page, rows, x, 124, chart_w, currency)
    _pdf_footer(page, section.source_refs, idx)


def _pdf_ratios(doc, section, idx):
    page = _pdf_page(doc, section.title, ACCENTS[0])
    row_h = 33.12
    for i, row in enumerate(section.body.get("rows", [])[:12]):
        y = 104.4 + i * row_h
        page.draw_rect(fitz.Rect(_PDF_MARGIN, y, _PDF_MARGIN + 5.76, y + row_h - 7.2), color=None, fill=_pdf_color(_accent(i)))
        _pdf_text(page, _PDF_MARGIN + 18, y + 4, 612, str(row.get("ratio", "")), size=13, max_height=row_h - 6)
        value = row.get("value")
        text = f"{value}{'%' if row.get('isPercentage') else ''}" if value is not None else ""
        _pdf_text(page, _PDF_W - _PDF_MARGIN - 187.2, y + 4, 172.8, text, size=13, color=ACCENTS[0], bold=True, align="right")
    _pdf_footer(page, section.source_refs, idx)


def _pdf_table(doc, section, idx, *, columns=None, rows=None, title=None):
    columns = columns or section.body.get("columns", [])
    rows = rows if rows is not None else section.body.get("rows", [])
    page = _pdf_page(doc, title or section.title, ACCENTS[5])
    if not columns:
        _pdf_text(page, _PDF_MARGIN, 108, _PDF_W - 2 * _PDF_MARGIN, "No data", size=14, color=MUTED)
        _pdf_footer(page, [], idx)
        return
    width = _PDF_W - 2 * _PDF_MARGIN
    weights = [max([len(str(name))] + [len(str(row[c])) if c < len(row) else 0 for row in rows] + [6]) for c, name in enumerate(columns)]
    weights = [min(w, 40) for w in weights]
    col_w = [width * w / sum(weights) for w in weights]
    cells = [[str(row[c]) if c < len(row) else "" for c in range(len(columns))] for row in rows]
    size = 10
    while True:
        heights = [max(len(_pdf_wrap(text, col_w[c] - 12, size)) for c, text in enumerate(row)) * size * 1.25 + 10 for row in cells]
        if 100.8 + 28 + sum(heights) <= _PDF_BOTTOM or size <= 7:
            break
        size -= 1
    y = 100.8
    page.draw_rect(fitz.Rect(_PDF_MARGIN, y, _PDF_MARGIN + width, y + 28), color=None, fill=_pdf_color(ACCENTS[5]))
    x = _PDF_MARGIN
    for c, name in enumerate(columns):
        _pdf_text(page, x + 6, y + 7, col_w[c] - 12, name, size=11, color=WHITE, bold=True, max_height=18, min_size=8)
        x += col_w[c]
    y += 28
    for r, row in enumerate(cells):
        if y + heights[r] > _PDF_BOTTOM:
            break
        if r % 2:
            page.draw_rect(fitz.Rect(_PDF_MARGIN, y, _PDF_MARGIN + width, y + heights[r]), color=None, fill=_pdf_color(_PDF_STRIPE))
        x = _PDF_MARGIN
        for c, text in enumerate(row):
            _pdf_text(page, x + 6, y + 5, col_w[c] - 12, text, size=size, max_height=heights[r] - 6, min_size=size)
            x += col_w[c]
        y += heights[r]
        page.draw_line((_PDF_MARGIN, y), (_PDF_MARGIN + width, y), color=_pdf_color(_PDF_GRID), width=0.6)
    _pdf_footer(page, section.source_refs, idx)


def _pdf_narrative(doc, section, idx):
    accent = RISK_RED if section.body.get("accent") == "risk" else ACCENTS[2]
    page = _pdf_page(doc, section.title, accent)
    bullets = [str(b) for b in section.body.get("bullets", []) if b][:12]
    _pdf_bullets(page, _PDF_MARGIN, 100.8, _PDF_W - 2 * _PDF_MARGIN, bullets, size=15, bullet_color=accent, max_y=489.6)
    _pdf_footer(page, section.source_refs, idx)


def _pdf_notes(doc, section, idx):
    page = _pdf_page(doc, section.title, ACCENTS[0])
    notes = section.body.get("notes", [])
    y = 97.2
    space = (_PDF_BOTTOM - y) / max(len(notes), 1)
    for note in notes:
        y = _pdf_text(page, _PDF_MARGIN, y, _PDF_W - 2 * _PDF_MARGIN, note.get("category", "").upper(), size=13, color=ACCENTS[0], bold=True)
        items = [str(i) for i in note.get("items", [])][:5]
        y = _pdf_bullets(page, _PDF_MARGIN + 10.8, y + 4, _PDF_W - 2 * _PDF_MARGIN - 10.8, items, size=12,
                         bullet_color=ACCENTS[0], max_y=min(_PDF_BOTTOM, y + space)) + 8
    _pdf_footer(page, section.source_refs, idx)


def _pdf_data_status(doc, section, idx):
    page = _pdf_page(doc, section.title, RISK_RED)
    y = 100.8
    conflicts = section.body.get("conflicts", [])
    missing = section.body.get("missing", [])
    if conflicts:
        y = _pdf_text(page, _PDF_MARGIN, y, _PDF_W - 2 * _PDF_MARGIN, "SOURCE CONFLICTS", size=13, color=RISK_RED, bold=True) + 4
        lines = [f"{c.get('field')}: sources disagree by ~{c.get('spreadPercent')}% for the same period (shown unresolved)" for c in conflicts]
        y = _pdf_bullets(page, _PDF_MARGIN + 10.8, y, _PDF_W - 2 * _PDF_MARGIN, lines, size=12, bullet_color=RISK_RED,
                         max_y=_PDF_BOTTOM if not missing else (y + _PDF_BOTTOM) / 2) + 14
    if missing:
        y = _pdf_text(page, _PDF_MARGIN, y, _PDF_W - 2 * _PDF_MARGIN, "NOT IDENTIFIED IN THE VERIFIED SOURCES", size=13, color=MUTED, bold=True) + 4
        _pdf_bullets(page, _PDF_MARGIN + 10.8, y, _PDF_W - 2 * _PDF_MARGIN, [m.get("message", m.get("label", "")) for m in missing],
                     size=12, color=MUTED)
    _pdf_footer(page, [], idx)


def _pdf_sources(doc, section, idx):
    page = _pdf_page(doc, section.title, ACCENTS[4])
    lines = []
    for r in section.body.get("reports", []):
        period = f" - {r.get('period')}" if r.get("period") and r.get("period") != "Undated report" else ""
        doc_type = f" ({r.get('documentType')})" if r.get("documentType") else ""
        lines.append(f"{r.get('filename', 'Uploaded report')}{period}{doc_type}")
    _pdf_bullets(page, _PDF_MARGIN, 104.4, _PDF_W - 2 * _PDF_MARGIN, lines, size=14, bullet_color=ACCENTS[4], max_y=403.2)
    external = section.body.get("external", {})
    if external.get("message"):
        _pdf_text(page, _PDF_MARGIN, _PDF_H - 72, _PDF_W - 2 * _PDF_MARGIN, external["message"], size=10, color=MUTED, max_height=30)
    _pdf_footer(page, [], idx)


_PDF_BUILDERS = {
    "summary": _pdf_summary,
    "documents": _pdf_documents,
    "kpi": _pdf_kpi,
    "line_chart": _pdf_line_chart,
    "pie": _pdf_breakdowns,
    "ratios": _pdf_ratios,
    "table": _pdf_table,
    "narrative": _pdf_narrative,
    "notes": _pdf_notes,
    "data_status": _pdf_data_status,
    "sources": _pdf_sources,
}


def _pdf_via_pymupdf(model: PresentationModel) -> bytes:
    doc = fitz.open()
    for idx, section in enumerate(model.sections, start=1):
        if section.kind == "title":
            _pdf_title(doc, section, idx)
            continue
        builder = _PDF_BUILDERS.get(section.kind)
        if builder is None:
            continue
        if section.kind == "table" and len(section.body.get("rows", [])) > 14:
            rows = section.body["rows"]
            for part, start in enumerate(range(0, len(rows), 14)):
                _pdf_table(doc, section, idx, columns=section.body["columns"], rows=rows[start:start + 14],
                           title=f"{section.title} ({part + 1})")
        else:
            builder(doc, section, idx)
    out = doc.tobytes(garbage=3, deflate=True)
    doc.close()
    return out


def validate_pdf(pdf_bytes: bytes, expected_page_count: int, *, exact: bool = True) -> int:

    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise ExportValidationError(f"Generated PDF could not be parsed: {exc}") from exc
    try:
        page_count = document.page_count
        if page_count == 0:
            raise ExportValidationError("Generated PDF has no pages")
        if exact and page_count != expected_page_count:
            raise ExportValidationError(
                f"PDF page count ({page_count}) does not match the presentation's slide count ({expected_page_count})"
            )
        if not exact and page_count < expected_page_count:
            raise ExportValidationError(
                f"PDF has fewer pages ({page_count}) than the presentation has slides ({expected_page_count})"
            )
        full_text = ""
        empty_pages = []
        for i in range(page_count):
            text = document[i].get_text().strip()
            if not text:
                empty_pages.append(i + 1)
            full_text += text + "\n"
        if empty_pages:
            raise ExportValidationError(f"PDF page(s) {empty_pages} converted with no readable content")
        for marker in ('{"field"', '"citations":', '"reportId"', "custom_id"):
            if marker in full_text:
                raise ExportValidationError(f"PDF contains raw data ({marker!r}) that must not reach a stakeholder file")
        return page_count
    finally:
        document.close()


def file_checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
