from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from app.services.pdf_mesh_renderer import generate_mesh_snapshots
from dfm import DFMReport
from fpdf import FPDF


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
LEFT = 48
RIGHT = 564
TOP = 720
BOTTOM = 54

# FaberAI Brand Design System Colors
PRIMARY = (0.031, 0.345, 0.957)       # #0858f4 - Faber Blue Accent
PRIMARY_DARK = (0.024, 0.263, 0.729)  # #0643ba - Deep Blue
NAVY = (0.027, 0.059, 0.369)          # #070f5e - Midnight Brand Navy
INK = (0.067, 0.094, 0.153)           # #111827 - Charcoal High-Contrast Text
MUTED = (0.392, 0.455, 0.545)         # #64748b - Sleek Cool-Gray Labels
LINE = (0.878, 0.906, 0.941)          # #e2e8f0 - Crisp Divider Gray
SURFACE = (0.969, 0.980, 0.992)       # #f7fafe - Soft Ice-Blue Surface
WHITE = (1.000, 1.000, 1.000)         # #ffffff - Pure White

# Severity & Metric Indicator Palette
PRO = (0.031, 0.345, 0.957)           # #0858f4 - Faber Blue Accent (Score >= 80)
WARN = (0.949, 0.600, 0.149)          # #f29926 - Amber Orange (Score 60-79)
FAIL = (0.910, 0.310, 0.310)          # #e84f4f - Crimson Red (Score < 60)
GREEN = (0.161, 0.651, 0.353)         # Backward compatible alias for emerald green

# Vector Logo Paths (from logo.svg, viewBox 1080 x 1080)
LOGO_PATH_NAVY = "m546 16q0.1 0.01 0.16 0.39l9.89-4.58 0.38 9.67-0.35 0.22 1.69 275.5c0.58 0.64 0.55 1.08 0.03 1.5-2.2 1.7-79.4 47.3-152.3 90.1-39.5 23.1-44.9 26.8-59.4 40.7-25.4 24.4-44 57.6-51.1 91.3-2.9 13.4-3.7 39.5-5 152.2-1.7 147-5 380.3-5.5 380.8-0.5 0.5-113.9-56.9-131-66.3-31.4-17.2-78.9-45.4-104.7-62.1l-9.8-6.4v-14.2c0-7.9 0.5-34.6 1-59.3 0.9-43.4 2.2-110.6 5.6-300.5 0.9-49.2 1.7-110.7 1.8-136.5 0.3-50.8 0.4-52.2 6.2-70 7.7-23.7 20.4-40.8 38.9-52.7 6.5-4.2 142.3-85.1 304-181.1 99.9-59.3 142.6-84.7 146-86.8 1.7-1 3.2-1.9 3.5-1.9zm-9.3 17.3c-5.1 2.9-42.7 25.3-83.7 49.7-41 24.3-90 53.5-109 64.8-19 11.3-53.2 31.6-76 45.2-22.8 13.6-56.1 33.4-74 44-106.3 63.1-106.5 63.2-115.6 75.3-8.7 11.5-16.6 31.2-19.4 48-1.6 9.8-2.2 26.6-1.3 33.7 0.5 3.6 0.6 23.4 0.2 44-0.8 36.8-1.9 100.2-3.9 222-0.6 33.8-1.9 104.7-3 157.5-1 52.8-1.8 96-1.7 96.1 0.1 0.1 8.5 5.3 18.7 11.6 33.9 21 71.3 42.9 98.6 57.6 16.2 8.7 107.5 54.5 107.9 54 0.2-0.3 1.7-102.1 3.6-249.3 0.6-46.2 1.6-122.5 2.4-169.5l1.3-85.5 2.6-12.2c8.6-40.6 30.1-77.3 61.1-104.5 11.8-10.3 17.7-14.1 72-46 25.3-14.9 63.3-37.3 84.5-49.8 21.2-12.5 40.6-23.9 43.2-25.4l4.33-2.54v-266.39l-3.93 2.39v-0.04z"
LOGO_PATH_BLUE = "m545.49 16c-0.3 3.3 0.31 24.5 0.71 40.5 1.5 66.5 2.8 152.7 2.8 192.6v42.6l49.8 31.3c27.3 17.3 81.7 51.6 120.7 76.3 39.1 24.8 75.6 47.9 81.3 51.4l10.2 6.4v143c0 78.6-0.4 142.9-0.8 142.9-0.5 0-23.5-13.6-51.3-30.1-45.1-27-121.1-72.2-176.4-105.1l-20-11.8-0.7 3.7c-0.4 2.1-3 21.6-5.8 43.3-2.7 21.7-7.2 56.8-9.9 78-2.8 21.2-6.8 52.7-9 70-2.3 17.3-5.9 45.4-8.1 62.5-2.2 17-3.7 31.2-3.2 31.5 0.8 0.7 25.1 15.6 199.7 122 68.6 41.8 77.3 47 78.4 47 1 0 45.8-25.7 199.9-114.7 25.9-15 48.6-28 50.3-28.9l3.1-1.6-0.6-112.6c-0.3-62-0.8-118.3-1.1-125.2-0.3-6.9-0.8-88-1.1-180.2-0.6-152.6-0.8-167.9-2.3-169.1-0.9-0.8-31.7-21.1-68.6-45.2-36.8-24.1-91.1-59.6-120.5-78.8-85.2-55.7-153.6-100.2-159.2-103.6-1.4-0.9-14.5-9.3-29-18.7-43.7-28.5-111.03-69.44-110.96-69.23 0.07 0.21-6.01 2.95-10.41 5.74z"


def _pdf_text(value: Any) -> str:
    text = "" if value is None else str(value)
    replacements = {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u00a0": " ",
        "\u2264": "<=",
        "\u2265": ">=",
        "\u00b0": " deg",
        "\u00b1": "+/-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _clean_filename(value: str | None) -> str:
    filename = value or "faberai-report"
    filename = re.sub(r"[^A-Za-z0-9._-]+", "-", filename).strip("-")
    return filename or "faberai-report"


def _fmt_number(value: Any, unit: str = "") -> str:
    if isinstance(value, (int, float)):
        return f"{value:,.2f}{unit}"
    return "Not available"


def _wrap(text: str, max_chars: int) -> list[str]:
    words = str(text).split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        if len(current) + len(word) + 1 > max_chars:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}"
    lines.append(current)
    return lines


def _rgb(color: tuple[float, float, float]) -> str:
    return f"{color[0]:.3f} {color[1]:.3f} {color[2]:.3f}"


def _score_color(score: Any) -> tuple[float, float, float]:
    if isinstance(score, (int, float)):
        val = float(score)
        if val >= 50:
            return GREEN
        if val >= 30:
            return WARN
        return FAIL
    return MUTED


def _svg_to_pdf(path_str: str, x0: float, y0: float, scale: float, view_height: float = 1080.0) -> list[str]:
    tokens = re.findall(r'[a-zA-DF-Z]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?', path_str)
    cmds: list[str] = []
    i = 0
    cur_x = 0.0
    cur_y = 0.0
    start_x = 0.0
    start_y = 0.0
    active_cmd = 'M'

    def to_pdf(sx: float, sy: float) -> tuple[float, float]:
        return (round(x0 + sx * scale, 3), round(y0 + (view_height - sy) * scale, 3))

    while i < len(tokens):
        token = tokens[i]
        if token.isalpha():
            active_cmd = token
            i += 1
            if active_cmd in ('Z', 'z'):
                cmds.append("h")
                cur_x, cur_y = start_x, start_y
            continue

        if active_cmd in ('m', 'M'):
            x = float(tokens[i])
                y = float(tokens[i+1])
            i += 2
            if active_cmd == 'm':
                cur_x += x
                cur_y += y
            else:
                cur_x, cur_y = x, y
            start_x, start_y = cur_x, cur_y
            px, py = to_pdf(cur_x, cur_y)
            cmds.append(f"{px} {py} m")
            active_cmd = 'l' if active_cmd == 'm' else 'L'
        elif active_cmd in ('l', 'L'):
            x = float(tokens[i])
                y = float(tokens[i+1])
            i += 2
            if active_cmd == 'l':
                cur_x += x
                cur_y += y
            else:
                cur_x, cur_y = x, y
            px, py = to_pdf(cur_x, cur_y)
            cmds.append(f"{px} {py} l")
        elif active_cmd in ('h', 'H'):
            x = float(tokens[i])
                i += 1
            cur_x = cur_x + x if active_cmd == 'h' else x
            px, py = to_pdf(cur_x, cur_y)
            cmds.append(f"{px} {py} l")
        elif active_cmd in ('v', 'V'):
            y = float(tokens[i])
                i += 1
            cur_y = cur_y + y if active_cmd == 'v' else y
            px, py = to_pdf(cur_x, cur_y)
            cmds.append(f"{px} {py} l")
        elif active_cmd in ('c', 'C'):
            x1 = float(tokens[i])
                y1 = float(tokens[i+1])
            x2 = float(tokens[i+2])
                y2 = float(tokens[i+3])
            x3 = float(tokens[i+4])
                y3 = float(tokens[i+5])
            i += 6
            if active_cmd == 'c':
                x1 += cur_x
                y1 += cur_y; x2 += cur_x; y2 += cur_y; x3 += cur_x; y3 += cur_y
            px1, py1 = to_pdf(x1, y1)
                px2, py2 = to_pdf(x2, y2); px3, py3 = to_pdf(x3, y3)
            cmds.append(f"{px1} {py1} {px2} {py2} {px3} {py3} c")
            cur_x, cur_y = x3, y3
        elif active_cmd in ('q', 'Q'):
            qx = float(tokens[i])
                qy = float(tokens[i+1])
            x3 = float(tokens[i+2])
                y3 = float(tokens[i+3])
            i += 4
            if active_cmd == 'q':
                qx += cur_x
                qy += cur_y; x3 += cur_x; y3 += cur_y
            x1 = cur_x + 2.0 / 3.0 * (qx - cur_x)
                y1 = cur_y + 2.0 / 3.0 * (qy - cur_y)
            x2 = x3 + 2.0 / 3.0 * (qx - x3)
                y2 = y3 + 2.0 / 3.0 * (qy - y3)
            px1, py1 = to_pdf(x1, y1)
                px2, py2 = to_pdf(x2, y2); px3, py3 = to_pdf(x3, y3)
            cmds.append(f"{px1} {py1} {px2} {py2} {px3} {py3} c")
            cur_x, cur_y = x3, y3
        else:
            i += 1
    return cmds


class _PDF:
    def __init__(self) -> None:
        self.doc = FPDF(orientation="P", unit="pt", format="letter")
        self.doc.pdf_version = "1.4"
        self.doc.set_title("Manufacturability report")
        self.doc.set_creator("FaberAI")
        self.doc.set_auto_page_break(False)
        self.pages: list[list[str]] = []
        
        font_dir = Path(__file__).resolve().parent.parent / "assets" / "fonts"
        if font_dir.exists() and (font_dir / "Geist-Regular.ttf").exists():
            self.doc.add_font("Geist", style="", fname=str(font_dir / "Geist-Regular.ttf"))
            self.doc.add_font("Geist", style="B", fname=str(font_dir / "Geist-Bold.ttf"))
            if (font_dir / "Geist-SemiBoldItalic.ttf").exists():
                self.doc.add_font("Geist", style="I", fname=str(font_dir / "Geist-SemiBoldItalic.ttf"))
            elif (font_dir / "Geist-Italic.ttf").exists():
                self.doc.add_font("Geist", style="I", fname=str(font_dir / "Geist-Italic.ttf"))
            if (font_dir / "Geist-BoldItalic.ttf").exists():
                self.doc.add_font("Geist", style="BI", fname=str(font_dir / "Geist-BoldItalic.ttf"))
            if (font_dir / "GeistMono-Regular.ttf").exists():
                self.doc.add_font("GeistMono", style="", fname=str(font_dir / "GeistMono-Regular.ttf"))
            if (font_dir / "GeistMono-Bold.ttf").exists():
                self.doc.add_font("GeistMono", style="B", fname=str(font_dir / "GeistMono-Bold.ttf"))
            self.font_regular = ("Geist", "")
            self.font_bold = ("Geist", "B")
            self.font_italic = ("Geist", "I")
            self.font_bold_italic = ("Geist", "BI")
            self.font_mono = ("GeistMono", "")
        else:
            self.font_regular = ("Helvetica", "")
            self.font_bold = ("Helvetica", "B")
            self.font_italic = ("Helvetica", "I")
            self.font_bold_italic = ("Helvetica", "BI")
            self.font_mono = ("Courier", "")

        self.y = TOP
        self.page_number = 0
        self.new_page()

    def _cmd(self, value: str) -> None:
        self.doc._out(value)

    def _page_header(self) -> None:
        self.rect(0, PAGE_HEIGHT - 6, PAGE_WIDTH, 6, fill=PRIMARY)
        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo-full.svg"
        if logo_path.exists():
            self.doc.image(str(logo_path), x=float(LEFT), y=18, w=82)
        else:
            self.draw_logo(LEFT, PAGE_HEIGHT - 38, size=24)
            self.text("FaberAI", LEFT + 30, PAGE_HEIGHT - 32, size=14, font="F2", color=NAVY)
        self.text("MANUFACTURABILITY REPORT", LEFT + 94, PAGE_HEIGHT - 31, size=7.5, font="F2", color=PRIMARY_DARK)
        self.text(f"PAGE {self.page_number:02d}", RIGHT - 54, PAGE_HEIGHT - 32, size=9, font="F2", color=MUTED)
        self.rect(LEFT, PAGE_HEIGHT - 48, RIGHT - LEFT, 1, fill=LINE)
        self.y = TOP - 6

    def draw_logo(self, x: float | int, y: float | int, size: float | int = 24) -> None:
        scale = float(size) / 1080.0
        cmds_navy = _svg_to_pdf(LOGO_PATH_NAVY, float(x), float(y), scale)
        cmds_blue = _svg_to_pdf(LOGO_PATH_BLUE, float(x), float(y), scale)
        if cmds_navy:
            self._cmd(f"{_rgb(NAVY)} rg " + " ".join(cmds_navy) + " f")
        if cmds_blue:
            self._cmd(f"{_rgb(PRIMARY)} rg " + " ".join(cmds_blue) + " f")
        self._cmd(f"{_rgb(INK)} rg")

    def new_page(self) -> None:
        self.doc.add_page()
        self.page_number += 1
        self._page_header()

    def ensure(self, height: int | float) -> None:
        if self.y - float(height) < BOTTOM:
            self.new_page()

    def rect(
        self,
        x: float | int,
        y: float | int,
        width: float | int,
        height: float | int,
        fill: tuple[float, float, float] | None = None,
        stroke: tuple[float, float, float] | None = None,
    ) -> None:
        style = ""
        if fill and stroke:
            style = "FD"
        elif fill:
            style = "F"
        elif stroke:
            style = "D"
        if style:
            if fill:
                self.doc.set_fill_color(int(fill[0] * 255), int(fill[1] * 255), int(fill[2] * 255))
            if stroke:
                self.doc.set_draw_color(int(stroke[0] * 255), int(stroke[1] * 255), int(stroke[2] * 255))
                self.doc.set_line_width(1)
            self.doc.rect(float(x), PAGE_HEIGHT - (float(y) + float(height)), float(width), float(height), style=style)

    def image(
        self,
        img_source: Any,
        x: float | int,
        y: float | int,
        width: float | int,
        height: float | int,
    ) -> None:
        self.doc.image(img_source, x=float(x), y=PAGE_HEIGHT - (float(y) + float(height)), w=float(width), h=float(height))

    def text(
        self,
        text: Any,
        x: float | int,
        y: float | int,
        size: float | int = 10,
        font: str = "F1",
        color: tuple[float, float, float] = INK,
    ) -> None:
        if font in ("F2", "bold"):
            fam, st = self.font_bold
        elif font in ("F3", "FI", "italic"):
            fam, st = self.font_italic
        elif font in ("F4", "FBI", "bold_italic"):
            fam, st = self.font_bold_italic
        elif font in ("FM", "mono"):
            fam, st = self.font_mono
        else:
            fam, st = self.font_regular
            
        self.doc.set_font(fam, style=st, size=float(size))
        self.doc.set_text_color(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))
        self.doc.text(float(x), PAGE_HEIGHT - float(y), _pdf_text(text))

    def line(self, text: Any, size: int = 10, font: str = "F1", gap: int = 14) -> None:
        self.ensure(gap)
        self.text(text, LEFT, self.y, size=size, font=font)
        self.y -= gap

    def muted(self, text: Any, size: int = 9, gap: int = 13) -> None:
        self.ensure(gap)
        self.text(text, LEFT, self.y, size=size, font="FI", color=MUTED)
        self.y -= gap

    def wrapped(
        self,
        text: Any,
        size: int = 10,
        font: str = "FI",
        max_chars: int = 86,
        color: tuple[float, float, float] = INK,
        indent: int | float = 0,
    ) -> None:
        for line in _wrap(str(text), max_chars):
            self.ensure(size + 5)
            self.text(line, LEFT + float(indent), self.y, size=size, font=font, color=color)
            self.y -= size + 5

    def section(self, title: str) -> None:
        self.ensure(36)
        self.y -= 10
        self.text(title.upper(), LEFT, self.y, size=11, font="F2", color=PRIMARY)
        self.y -= 10
        self.rect(LEFT, self.y, RIGHT - LEFT, 1, fill=LINE)
        self.rect(LEFT, self.y, 36, 2, fill=PRIMARY)
        self.y -= 16

    def spacer(self, amount: int = 8) -> None:
        self.y -= amount

    def key_value_grid(self, values: list[tuple[str, str]], columns: int = 2) -> None:
        width = (RIGHT - LEFT - 12) // columns
        row_height = 42
        for index, (label, value) in enumerate(values):
            if index % columns == 0:
                self.ensure(row_height + 8)
                row_y = self.y - row_height + 12
            x = LEFT + (index % columns) * (width + 12)
            self.rect(x, row_y, width, row_height, fill=SURFACE, stroke=LINE)
            self.text(label.upper(), x + 10, row_y + 24, size=7, font="F2", color=MUTED)
            self.text(value, x + 10, row_y + 10, size=10, font="F2", color=INK)
            if index % columns == columns - 1 or index == len(values) - 1:
                self.y -= row_height + 10

    def get_width(self, text: Any, size: float | int = 10, font: str = "F1") -> float:
        if font in ("F2", "bold"):
            fam, st = self.font_bold
        elif font in ("F3", "FI", "italic"):
            fam, st = self.font_italic
        elif font in ("F4", "FBI", "bold_italic"):
            fam, st = self.font_bold_italic
        elif font in ("FM", "mono"):
            fam, st = self.font_mono
        else:
            fam, st = self.font_regular
        self.doc.set_font(fam, style=st, size=float(size))
        return float(self.doc.get_string_width(_pdf_text(text)))

    def tag(
        self,
        text: Any,
        x: float | int,
        y: float | int,
        base_color: tuple[float, float, float] = PRIMARY,
        size: float | int = 8.5,
        font: str = "F2",
        padding_x: float | int = 6,
        height: float | int = 15,
    ) -> float:
        w = self.get_width(text, size=size, font=font)
        badge_width = w + (padding_x * 2)
        bg = (0.86 + 0.14 * base_color[0], 0.86 + 0.14 * base_color[1], 0.86 + 0.14 * base_color[2])
        self.doc.set_fill_color(int(bg[0] * 255), int(bg[1] * 255), int(bg[2] * 255))
        box_y = PAGE_HEIGHT - float(y) - 3.0 - (float(height) / 2.0)
        self.doc.rect(float(x), box_y, badge_width, float(height), style="F")
        self.text(text, float(x) + float(padding_x), float(y), size=size, font=font, color=base_color)
        return badge_width

    def score_card(self, label: str, score: Any, subtitle: str, x: float | int, y: float | int, width: float | int) -> None:
        color = _score_color(score)
        self.rect(x, y, width, 76, fill=SURFACE, stroke=LINE)
        self.rect(x, y, 4, 76, fill=color)
        
        score_val = f"{round(float(score))}" if isinstance(score, (int, float)) else "N/A"
        self.text(score_val, x + 16, y + 42, size=24, font="F2", color=color)
        val_w = self.get_width(score_val, size=24, font="F2")
        self.text("/ 100", x + 16 + val_w + 6, y + 44, size=11, font="F1", color=MUTED)
        
        self.text(label.upper(), x + 16, y + 24, size=9.5, font="F2", color=INK)
        self.text(subtitle, x + 16, y + 10, size=8, font="FI", color=MUTED)

    def render(self) -> bytes:
        return bytes(self.doc.output())


def report_pdf_filename(analysis: dict[str, Any]) -> str:
    stem = _clean_filename(analysis.get("filename"))
    if "." in stem:
        stem = stem.rsplit(".", 1)[0]
    return f"{stem}-dfm-report.pdf"


def _unique_strings(values: list[str], limit: int) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = " ".join(str(value).split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
        if len(result) >= limit:
            break
    return result


def _legacy_issue_text(issue: dict[str, Any]) -> str:
    return (
        issue.get("message")
        or issue.get("description")
        or issue.get("title")
        or issue.get("type")
        or "Manufacturability issue"
    )


def _legacy_issue_recommendation(issue: dict[str, Any]) -> str:
    return issue.get("recommendation") or "Review this issue against the highlighted DFM rule."


def build_report_pdf(analysis: dict[str, Any], include_comparison: bool = False) -> bytes:
    report_payload = analysis.get("dfm_report")
    report = DFMReport.model_validate(report_payload) if report_payload else None

    pdf = _PDF()
    filename = analysis.get("filename") or (report.part.filename if report else None)
    analysis_id = analysis.get("analysis_id") or (report.analysis_id if report else None)
    score = analysis.get("manufacturability_score")
    if score is None and report is not None:
        score = report.manufacturability_score

    pdf.text("DFM INSPECTION SUMMARY", LEFT, pdf.y, size=9, font="F2", color=PRIMARY)
    pdf.y -= 26
    pdf.text("Manufacturability report", LEFT, pdf.y, size=22, font="F2", color=INK)
    pdf.y -= 22
    pdf.wrapped(
        "Supplier-ready DFM analysis generated from definitive manufacturing design evaluations.",
        size=10,
        max_chars=78,
        color=MUTED,
    )
    pdf.spacer(8)

    pdf.key_value_grid(
        [
            ("File", filename or "Unknown file"),
            ("Analysis ID", str(analysis_id or "Not available")),
            ("Generated", datetime.now().strftime("%Y-%m-%d %H:%M")),
            ("Report type", "Molding vs printing" if include_comparison else "Selected process"),
        ],
        columns=2,
    )

    snapshots = generate_mesh_snapshots(analysis)
    if len(snapshots) >= 4:
        pdf.section("3D Model Preview")
        cell_w = (RIGHT - LEFT - 12) // 2
        cell_h = 160
        pdf.ensure((cell_h * 2) + 24)
        top_y = pdf.y - cell_h
        for idx in range(4):
            col = idx % 2
            row = idx // 2
            x = LEFT + col * (cell_w + 12)
            y = top_y - row * (cell_h + 12)
            pdf.rect(x, y, cell_w, cell_h, fill=SURFACE, stroke=LINE)
            pdf.image(snapshots[idx], x + 2, y + 2, cell_w - 4, cell_h - 4)
        pdf.y = top_y - (cell_h + 12) - 16

    pdf.section("Verdict")
    pdf.ensure(116)
    card_y = pdf.y - 110
    score_col = _score_color(score)
    pdf.rect(LEFT, card_y, RIGHT - LEFT, 110, fill=SURFACE, stroke=LINE)
    pdf.rect(LEFT, card_y, 6, 110, fill=score_col)
    score_text = f"{round(float(score))}" if isinstance(score, (int, float)) else "N/A"
    pdf.text(score_text, LEFT + 22, card_y + 60, size=34, font="F2", color=score_col)
    score_w = pdf.get_width(score_text, size=34, font="F2")
    pdf.text("/ 100", LEFT + 22 + score_w + 8, card_y + 63, size=13, font="F1", color=MUTED)
    pdf.text("OVERALL MANUFACTURABILITY RATING", LEFT + 22, card_y + 28, size=7.5, font="F2", color=MUTED)
    summary = analysis.get("summary") or (
        "Completed DFM report." if report is not None else "No DFM report summary was supplied."
    )
    summary_lines = _wrap(str(summary), 46)[:3]
    for index, line in enumerate(summary_lines):
        pdf.text(line, LEFT + 220, card_y + 82 - index * 16, size=10.5, font="FI", color=INK)
    if report is not None:
        recommendation = report.recommendation.reason or "No process preference was reported."
        rec_y = card_y + 82 - (len(summary_lines) * 16) - 12
        for index, line in enumerate(_wrap(f"Recommendation: {recommendation}", 50)[:3]):
            pdf.text(line, LEFT + 220, rec_y - index * 14, size=8.5, font="FI", color=MUTED)
    pdf.y = card_y - 18

    if report is not None:
        pdf.section("Part summary")
        part = report.part
        bbox = (
            " x ".join(f"{value:.2f}" for value in part.bounding_box_mm) + " mm"
            if part.bounding_box_mm
            else "Not available"
        )
        pdf.key_value_grid(
            [
                ("Units", part.units),
                ("Volume", _fmt_number(part.volume_mm3, " mm3")),
                ("Surface area", _fmt_number(part.surface_area_mm2, " mm2")),
                ("Bounding box", bbox),
                ("Faces", str(part.face_count)),
                ("Measurements reliable", "Yes" if part.measurements_reliable else "No"),
            ],
            columns=3,
        )

        processes = report.processes if include_comparison else report.processes[:1]
        pdf.section("Process results")
        pdf.ensure(90)
        card_width = (RIGHT - LEFT - 12) // 2
        row_y = pdf.y - 78
        for index, process in enumerate(processes):
            x = LEFT + (index % 2) * (card_width + 12)
            if index > 0 and index % 2 == 0:
                pdf.y = row_y - 14
                pdf.ensure(90)
                row_y = pdf.y - 78
                x = LEFT
            pdf.score_card(
                process.process.value.replace("_", " ").title(),
                process.score,
                f"{process.verdict_label or 'Completed'} - {round(process.confidence * 100)}% confidence",
                x,
                row_y,
                card_width,
            )
        pdf.y = row_y - 18

        pdf.new_page()
        pdf.section("Process comparison")
        for process in processes:
            failed = [rule for rule in process.rule_results if rule.status.value == "fail"]
            not_assessed = [
                rule for rule in process.rule_results if rule.status.value == "not_assessed"
            ]
            passed = [rule for rule in process.rule_results if rule.status.value == "pass"]
            pdf.ensure(58)
            proc_name = process.process.value.replace("_", " ").title()
            tag_text = f"{proc_name.upper()} [M]" if "molding" in proc_name.lower() else (f"{proc_name.upper()} [P]" if "print" in proc_name.lower() else proc_name.upper())
            tag_color = WARN if "molding" in proc_name.lower() else PRIMARY
            badge_w = pdf.tag(tag_text, LEFT, pdf.y, base_color=tag_color, size=9, font="F2", padding_x=8, height=17)
            score_str = f"{round(float(process.score))}" if isinstance(process.score, (int, float)) else "N/A"
            pdf.text(score_str, LEFT + badge_w + 14, pdf.y, size=10.5, font="F2", color=_score_color(process.score))
            score_w = pdf.get_width(score_str, size=10.5, font="F2")
            pdf.text(
                f"/ 100 - {process.verdict_label or 'Completed'}",
                LEFT + badge_w + 14 + score_w + 4,
                pdf.y,
                size=10.5,
                font="F2",
                color=INK,
            )
            pdf.y -= 18
            pdf.wrapped(
                f"Rules: {len(passed)} passed, {len(failed)} failed, "
                f"{len(not_assessed)} not assessed. Confidence: {round(process.confidence * 100)}%.",
                max_chars=92,
                color=MUTED,
            )
            if process.assumptions:
                pdf.wrapped(
                    f"Key assumption: {process.assumptions[0]}",
                    max_chars=92,
                    color=MUTED,
                )
            pdf.spacer(6)

        for process in processes:
            failed_rules = [rule for rule in process.rule_results if rule.status.value == "fail"]
            pdf.ensure(34)
            proc_name = process.process.value.replace("_", " ").title()
            tag_label = f"[{'M' if 'molding' in proc_name.lower() else ('P' if 'print' in proc_name.lower() else 'i')}]"
            proc_color = WARN if "molding" in proc_name.lower() else PRIMARY
            badge_w = pdf.tag(f"{proc_name.upper()} {tag_label}", LEFT, pdf.y, base_color=proc_color, size=9, font="F2", padding_x=8, height=16)
            pdf.text("FAILED RULES", LEFT + badge_w + 8, pdf.y, size=10, font="F2", color=INK)
            pdf.y -= 18
            if failed_rules:
                for rule in failed_rules[:8]:
                    pdf.ensure(44)
                    color = FAIL if rule.severity and rule.severity.value == "blocker" else WARN
                    tag_text = f"[{rule.rule_id}]" if not str(rule.rule_id).startswith("[") else str(rule.rule_id)
                    badge_w = pdf.tag(tag_text, LEFT, pdf.y, base_color=color, size=8.5, font="F2", padding_x=6, height=15)
                    pdf.text(rule.name, LEFT + badge_w + 8, pdf.y, size=10, font="F2", color=INK)
                    pdf.y -= 15
                    pdf.wrapped(
                        rule.summary or rule.explanation or "No explanation available.",
                        size=9,
                        max_chars=82,
                        color=MUTED,
                        indent=12,
                    )
                    pdf.spacer(8)
            else:
                pdf.muted("No failed rules reported.")
            pdf.spacer(8)

        pdf.section("Rule evidence")
        for process in processes:
            pdf.ensure(32)
            proc_name = process.process.value.replace("_", " ").title()
            tag_text = f"{proc_name.upper()} [M]" if "molding" in proc_name.lower() else (f"{proc_name.upper()} [P]" if "print" in proc_name.lower() else proc_name.upper())
            tag_color = WARN if "molding" in proc_name.lower() else PRIMARY
            pdf.tag(tag_text, LEFT, pdf.y, base_color=tag_color, size=9.5, font="F2", padding_x=8, height=17)
            pdf.y -= 18
            for rule in process.rule_results:
                pdf.ensure(44)
                status = rule.status.value.replace("_", " ").upper()
                color = FAIL if rule.status.value == "fail" else (WARN if rule.status.value == "warn" else PRIMARY)
                tag_text = f"[{rule.rule_id}]" if not str(rule.rule_id).startswith("[") else str(rule.rule_id)
                badge_w = pdf.tag(tag_text, LEFT, pdf.y, base_color=color, size=8.5, font="F2", padding_x=6, height=15)
                pdf.text(rule.name, LEFT + badge_w + 8, pdf.y, size=10, font="F2", color=INK)
                status_text = f"{status} | IMPACT {rule.score_impact:.1f}"
                pdf.tag(status_text, LEFT + 340, pdf.y, base_color=color, size=8, font="F2", padding_x=6, height=15)
                pdf.y -= 16
                pdf.wrapped(rule.summary or rule.explanation or "No summary supplied.", size=9, max_chars=82, indent=12)
                if rule.recommendations:
                    pdf.wrapped(
                        f"Recommended action: {rule.recommendations[0]}",
                        size=9,
                        max_chars=82,
                        color=MUTED,
                        indent=12,
                    )
                pdf.spacer(6)

        findings = [
            finding
            for process in report.processes
            for rule in process.rule_results
            if rule.status.value == "fail"
            for finding in rule.findings
        ]
        if findings:
            pdf.section("Top findings")
            shown_findings = findings[:14]
            pdf.muted(f"Showing the top {len(shown_findings)} of {len(findings)} findings.")
            for finding in shown_findings:
                pdf.ensure(44)
                color = FAIL if finding.severity.value == "blocker" else WARN
                tag_text = f"[{finding.rule_id}]" if not str(finding.rule_id).startswith("[") else str(finding.rule_id)
                badge_w = pdf.tag(tag_text, LEFT, pdf.y, base_color=color, size=8.5, font="F2", padding_x=6, height=15)
                pdf.text(finding.severity.value.upper(), LEFT + badge_w + 8, pdf.y, size=9.5, font="F2", color=color)
                pdf.y -= 15
                pdf.wrapped(
                    finding.message,
                    size=9,
                    max_chars=82,
                    indent=12,
                )
                pdf.wrapped(f"Recommendation: {finding.recommendation}", size=9, max_chars=82, color=MUTED, indent=12)
                pdf.spacer(6)

        recommendations = _unique_strings(
            [
                recommendation
                for process in report.processes
                for rule in process.rule_results
                for recommendation in rule.recommendations
            ]
            + [
                finding.recommendation
                for process in report.processes
                for rule in process.rule_results
                for finding in rule.findings
            ],
            limit=9,
        )
        if recommendations:
            pdf.section("Recommended improvements")
            for index, recommendation in enumerate(recommendations, start=1):
                pdf.ensure(34)
                pdf.wrapped(f"{index}. {recommendation}", max_chars=92)

        if report.warnings:
            pdf.section("Warnings")
            for warning in report.warnings[:8]:
                pdf.wrapped(warning, max_chars=92)

    elif analysis.get("issues"):
        issues = [issue for issue in analysis["issues"] if isinstance(issue, dict)]
        severity_counts: dict[str, int] = {}
        for issue in issues:
            severity = str(issue.get("severity") or "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        pdf.section("Issue summary")
        pdf.wrapped(
            f"The export contains {len(issues)} visible issue(s): "
            + ", ".join(f"{count} {severity}" for severity, count in severity_counts.items()),
            max_chars=92,
        )
        pdf.section("Top issues")
        for issue in issues[:24]:
            pdf.ensure(44)
            severity_str = str(issue.get("severity") or "issue").upper()
            badge_w = pdf.tag(severity_str, LEFT, pdf.y, base_color=PRIMARY, size=8, font="F2", padding_x=6, height=15)
            pdf.y -= 2
            pdf.wrapped(_legacy_issue_text(issue), font="F2", max_chars=74, indent=badge_w + 8)
            pdf.wrapped(f"Recommendation: {_legacy_issue_recommendation(issue)}", color=MUTED, size=9, max_chars=82, indent=12)
            pdf.spacer(6)

        recommendations = _unique_strings(
            [_legacy_issue_recommendation(issue) for issue in issues],
            limit=12,
        )
        if recommendations:
            pdf.section("Recommended improvements")
            for index, recommendation in enumerate(recommendations, start=1):
                pdf.wrapped(f"{index}. {recommendation}", max_chars=92)

    return pdf.render()
