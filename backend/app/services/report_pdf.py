from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from dfm import DFMReport


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
LEFT = 48
RIGHT = 564
TOP = 730
BOTTOM = 54
GREEN = (0.118, 0.541, 0.361)
MINT = (0.435, 1.0, 0.690)
INK = (0.060, 0.078, 0.065)
MUTED = (0.430, 0.470, 0.440)
LINE = (0.840, 0.870, 0.850)
SURFACE = (0.956, 0.972, 0.960)
WARN = (0.900, 0.640, 0.240)
FAIL = (0.910, 0.310, 0.310)


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
    text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return text.encode("latin-1", "replace").decode("latin-1")


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


class _PDF:
    def __init__(self) -> None:
        self.pages: list[list[str]] = [[]]
        self.y = TOP
        self.page_number = 1
        self._page_header()

    def _cmd(self, value: str) -> None:
        self.pages[-1].append(value)

    def _page_header(self) -> None:
        self._cmd(f"{_rgb(GREEN)} rg 0 {PAGE_HEIGHT - 18} {PAGE_WIDTH} 18 re f")
        self._cmd(f"{_rgb(INK)} rg")
        self.text("FaberAI", LEFT, PAGE_HEIGHT - 46, size=11, font="F2", color=GREEN)
        self.text(f"DFM report - Page {self.page_number}", RIGHT - 112, PAGE_HEIGHT - 46, size=8, color=MUTED)
        self.y = TOP - 10

    def new_page(self) -> None:
        self.pages.append([])
        self.page_number += 1
        self._page_header()

    def ensure(self, height: int) -> None:
        if self.y - height < BOTTOM:
            self.new_page()

    def rect(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        fill: tuple[float, float, float] | None = None,
        stroke: tuple[float, float, float] | None = None,
    ) -> None:
        if fill:
            self._cmd(f"{_rgb(fill)} rg {x} {y} {width} {height} re f")
        if stroke:
            self._cmd(f"{_rgb(stroke)} RG {x} {y} {width} {height} re S")

    def text(
        self,
        text: Any,
        x: int,
        y: int,
        size: int = 10,
        font: str = "F1",
        color: tuple[float, float, float] = INK,
    ) -> None:
        self._cmd(f"BT {_rgb(color)} rg /{font} {size} Tf 1 0 0 1 {x} {y} Tm ({_pdf_text(text)}) Tj ET")

    def line(self, text: Any, size: int = 10, font: str = "F1", gap: int = 14) -> None:
        self.ensure(gap)
        self.text(text, LEFT, self.y, size=size, font=font)
        self.y -= gap

    def muted(self, text: Any, size: int = 9, gap: int = 13) -> None:
        self.ensure(gap)
        self.text(text, LEFT, self.y, size=size, color=MUTED)
        self.y -= gap

    def wrapped(
        self,
        text: Any,
        size: int = 10,
        font: str = "F1",
        max_chars: int = 86,
        color: tuple[float, float, float] = INK,
    ) -> None:
        for line in _wrap(str(text), max_chars):
            self.ensure(size + 5)
            self.text(line, LEFT, self.y, size=size, font=font, color=color)
            self.y -= size + 5

    def section(self, title: str) -> None:
        self.ensure(34)
        self.y -= 8
        self.text(title, LEFT, self.y, size=13, font="F2", color=GREEN)
        self.y -= 11
        self.rect(LEFT, self.y, RIGHT - LEFT, 1, fill=LINE)
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
            self.text(label, x + 10, row_y + 24, size=7, color=MUTED)
            self.text(value, x + 10, row_y + 10, size=10, font="F2", color=INK)
            if index % columns == columns - 1 or index == len(values) - 1:
                self.y -= row_height + 10

    def score_card(self, label: str, score: Any, subtitle: str, x: int, y: int, width: int) -> None:
        self.rect(x, y, width, 74, fill=SURFACE, stroke=LINE)
        score_text = f"{round(float(score))}/100" if isinstance(score, (int, float)) else "N/A"
        self.text(score_text, x + 12, y + 43, size=20, font="F2", color=GREEN)
        self.text(label, x + 12, y + 24, size=10, font="F2")
        self.text(subtitle, x + 12, y + 10, size=8, color=MUTED)

    def render(self) -> bytes:
        objects: list[bytes] = []

        def add_object(payload: bytes) -> int:
            objects.append(payload)
            return len(objects)

        catalog_id = add_object(b"<< /Type /Catalog /Pages 2 0 R >>")
        pages_placeholder_id = add_object(b"")
        font_regular_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        font_bold_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

        page_ids: list[int] = []
        for page_lines in self.pages:
            commands = page_lines
            content = "\n".join(commands).encode("latin-1", "replace")
            content_id = add_object(
                b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream"
            )
            page_id = add_object(
                (
                    f"<< /Type /Page /Parent {pages_placeholder_id} 0 R "
                    f"/MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                    f"/Resources << /Font << /F1 {font_regular_id} 0 R /F2 {font_bold_id} 0 R >> >> "
                    f"/Contents {content_id} 0 R >>"
                ).encode()
            )
            page_ids.append(page_id)

        kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
        objects[pages_placeholder_id - 1] = (
            f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"
        ).encode()

        chunks = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
        offsets: list[int] = []
        for i, payload in enumerate(objects, start=1):
            offsets.append(sum(len(chunk) for chunk in chunks))
            chunks.append(f"{i} 0 obj\n".encode() + payload + b"\nendobj\n")

        xref_offset = sum(len(chunk) for chunk in chunks)
        chunks.append(f"xref\n0 {len(objects) + 1}\n".encode())
        chunks.append(b"0000000000 65535 f \n")
        for offset in offsets:
            chunks.append(f"{offset:010d} 00000 n \n".encode())
        chunks.append(
            (
                f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
                f"startxref\n{xref_offset}\n%%EOF\n"
            ).encode()
        )
        return b"".join(chunks)


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

    pdf.text("Manufacturability report", LEFT, pdf.y, size=22, font="F2")
    pdf.y -= 22
    pdf.wrapped(
        "Supplier-ready DFM summary generated from the completed deterministic analysis.",
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

    pdf.section("Verdict")
    pdf.ensure(92)
    card_y = pdf.y - 88
    pdf.rect(LEFT, card_y, RIGHT - LEFT, 88, fill=SURFACE, stroke=LINE)
    score_text = f"{round(float(score))}" if isinstance(score, (int, float)) else "N/A"
    pdf.text(score_text, LEFT + 18, card_y + 35, size=32, font="F2", color=GREEN)
    pdf.text("/100", LEFT + 72, card_y + 40, size=11, color=MUTED)
    pdf.text("Overall manufacturability score", LEFT + 18, card_y + 18, size=9, color=MUTED)
    summary = analysis.get("summary") or (
        "Completed DFM report." if report is not None else "No DFM report summary was supplied."
    )
    for index, line in enumerate(_wrap(str(summary), 58)[:3]):
        pdf.text(line, LEFT + 170, card_y + 49 - index * 14, size=10)
    if report is not None:
        recommendation = report.recommendation.reason or "No process preference was reported."
        for index, line in enumerate(_wrap(f"Recommendation: {recommendation}", 58)[:3]):
            pdf.text(line, LEFT + 170, card_y + 24 - index * 12, size=8, color=MUTED)
    pdf.y = card_y - 14

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

        pdf.section("Process comparison")
        for process in processes:
            failed = [rule for rule in process.rule_results if rule.status.value == "fail"]
            not_assessed = [
                rule for rule in process.rule_results if rule.status.value == "not_assessed"
            ]
            passed = [rule for rule in process.rule_results if rule.status.value == "pass"]
            pdf.ensure(58)
            pdf.text(
                process.process.value.replace("_", " ").title(),
                LEFT,
                pdf.y,
                size=11,
                font="F2",
            )
            pdf.text(
                f"{round(process.score)}/100 - {process.verdict_label or 'Completed'}",
                LEFT + 190,
                pdf.y,
                size=10,
                font="F2",
                color=GREEN,
            )
            pdf.y -= 15
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
            pdf.spacer(4)

        for process in processes:
            failed_rules = [rule for rule in process.rule_results if rule.status.value == "fail"]
            pdf.ensure(34)
            pdf.text(
                f"{process.process.value.replace('_', ' ').title()} failed rules",
                LEFT,
                pdf.y,
                size=11,
                font="F2",
            )
            pdf.y -= 17
            if failed_rules:
                for rule in failed_rules[:8]:
                    pdf.ensure(40)
                    color = FAIL if rule.severity and rule.severity.value == "blocker" else WARN
                    pdf.rect(LEFT, pdf.y - 6, 6, 6, fill=color)
                    pdf.wrapped(
                        f"{rule.rule_id} {rule.name}: {rule.summary or rule.explanation}",
                        max_chars=92,
                    )
            else:
                pdf.muted("No failed rules reported.")
            pdf.spacer(8)

        pdf.section("Rule evidence")
        for process in processes:
            pdf.ensure(30)
            pdf.text(
                process.process.value.replace("_", " ").title(),
                LEFT,
                pdf.y,
                size=11,
                font="F2",
            )
            pdf.y -= 16
            for rule in process.rule_results:
                pdf.ensure(34)
                status = rule.status.value.replace("_", " ")
                severity = rule.severity.value if rule.severity else "none"
                pdf.text(
                    f"{rule.rule_id} {rule.name}",
                    LEFT,
                    pdf.y,
                    size=9,
                    font="F2",
                )
                pdf.text(
                    f"{status} / {severity} / impact {rule.score_impact:.1f}",
                    LEFT + 270,
                    pdf.y,
                    size=8,
                    color=MUTED,
                )
                pdf.y -= 13
                pdf.wrapped(rule.summary or rule.explanation or "No summary supplied.", max_chars=92)
                if rule.recommendations:
                    pdf.wrapped(
                        f"Recommended action: {rule.recommendations[0]}",
                        max_chars=92,
                        color=MUTED,
                    )
                pdf.spacer(3)

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
                pdf.ensure(50)
                pdf.wrapped(
                    f"{finding.rule_id} [{finding.severity.value}] {finding.message}",
                    font="F2",
                    max_chars=92,
                )
                pdf.wrapped(f"Recommendation: {finding.recommendation}", max_chars=92, color=MUTED)
                pdf.spacer(4)

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
            pdf.ensure(40)
            pdf.wrapped(_legacy_issue_text(issue), font="F2", max_chars=92)
            pdf.wrapped(f"Recommendation: {_legacy_issue_recommendation(issue)}", color=MUTED)
            pdf.spacer(4)

        recommendations = _unique_strings(
            [_legacy_issue_recommendation(issue) for issue in issues],
            limit=12,
        )
        if recommendations:
            pdf.section("Recommended improvements")
            for index, recommendation in enumerate(recommendations, start=1):
                pdf.wrapped(f"{index}. {recommendation}", max_chars=92)

    return pdf.render()
