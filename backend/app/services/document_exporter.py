"""CONVELINA — Phase P3G.4 Professional Document Exporter Service

Exports personalized administrative correction drafts into high-fidelity,
professionally styled PDF and DOCX files with:
- Full Unicode support including authentic Tamil (Lohit Tamil) and Devanagari/Latin (DejaVu Sans).
- Automatic script detection (Tamil vs Latin).
- Clean A4 page layout with 0.75-inch (54pt) margins and consistent typography.
- Two-pass NumberedCanvas with "Page X of Y" dynamic numbering.
- Diagonal background watermark: "ADMINISTRATIVE DRAFT — NOT OFFICIAL".
- Prominent statutory draft disclaimer banner.
- Structured discrepancy tables and bulleted enclosure checklists.
- SHA-256 cryptographic integrity verification stamp in footer/metadata.
- Substantive content equivalence between PDF and DOCX.
- Zero fake government emblems, seals, stamps, or fabricated approval marks.
"""

import io
import os
import re
import hashlib
from typing import Optional, List, Tuple

DRAFT_WATERMARK_TEXT = (
    "AI-GENERATED ADMINISTRATIVE DRAFT — REVIEW ALL DETAILS AND VERIFY THE APPLICABLE OFFICIAL PROCEDURE BEFORE SUBMISSION."
)

WATERMARK_DIAGONAL_TEXT = "ADMINISTRATIVE DRAFT — NOT OFFICIAL"

# Font paths in container / standard Linux environments
LOHIT_TAMIL_PATHS = [
    "/usr/share/fonts/truetype/lohit-tamil/Lohit-Tamil.ttf",
    "/usr/share/fonts/lohit-tamil/Lohit-Tamil.ttf",
]
FREE_SANS_PATHS = [
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/freefont/FreeSans.ttf",
]
FREE_SANS_BOLD_PATHS = [
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/freefont/FreeSansBold.ttf",
]
DEJAVU_SANS_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
]
DEJAVU_BOLD_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]

_fonts_registered = False


def _register_export_fonts():
    """Registers Unicode TrueType fonts with ReportLab if available."""
    global _fonts_registered
    if _fonts_registered:
        return

    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        for p in FREE_SANS_PATHS:
            if os.path.exists(p):
                pdfmetrics.registerFont(TTFont("FreeSans", p))
                pdfmetrics.registerFontFamily("FreeSans", normal="FreeSans", bold="FreeSans", italic="FreeSans", boldItalic="FreeSans")
                break

        for p in LOHIT_TAMIL_PATHS:
            if os.path.exists(p):
                pdfmetrics.registerFont(TTFont("LohitTamil", p))
                break

        for p in DEJAVU_SANS_PATHS:
            if os.path.exists(p):
                pdfmetrics.registerFont(TTFont("DejaVuSans", p))
                break

        for p in DEJAVU_BOLD_PATHS:
            if os.path.exists(p):
                pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", p))
                break

        _fonts_registered = True
    except Exception:
        # Fallback to standard PDF core fonts if TrueType registration fails
        pass


def detect_text_script(text: str) -> str:
    """Detects primary language script of content."""
    if re.search(r"[\u0B80-\u0BFF]", text):
        return "tamil"
    if re.search(r"[\u0900-\u097F]", text):
        return "devanagari"
    return "latin"


class DocumentExporter:
    """Exports structured correction representations to print-ready PDF and editable DOCX."""

    @staticmethod
    def export_pdf(
        title: str,
        content: str,
        draft_id: Optional[str] = None,
        language: str = "en",
    ) -> bytes:
        """Generates a professionally formatted, Unicode-compliant PDF with ReportLab."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import (
                SimpleDocTemplate,
                Paragraph,
                Spacer,
                HRFlowable,
                Table,
                TableStyle,
                KeepTogether,
            )
            from reportlab.pdfgen import canvas
        except ImportError:
            raise RuntimeError("ReportLab is required for PDF export. Please install reportlab.")

        _register_export_fonts()

        # Compute content hash
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # Detect script and select font
        from reportlab.pdfbase import pdfmetrics
        registered_fonts = pdfmetrics.getRegisteredFontNames()
        script = detect_text_script(content + " " + title)
        has_indic = script in ("tamil", "devanagari") or language in ("ta", "hi", "bilingual_en_ta")

        if has_indic and "FreeSans" in registered_fonts:
            font_family = "FreeSans"
            bold_font_family = "FreeSans"
        elif script == "tamil" and "LohitTamil" in registered_fonts:
            font_family = "LohitTamil"
            bold_font_family = "LohitTamil"
        elif "DejaVuSans" in registered_fonts:
            font_family = "DejaVuSans"
            bold_font_family = "DejaVuSans-Bold" if "DejaVuSans-Bold" in registered_fonts else "DejaVuSans"
        else:
            font_family = "Helvetica"
            bold_font_family = "Helvetica-Bold"

        buffer = io.BytesIO()

        # Custom NumberedCanvas with watermark & dynamic footer
        class NumberedCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._saved_page_states = []

            def showPage(self):
                self._saved_page_states.append(dict(self.__dict__))
                self._startPage()

            def save(self):
                num_pages = len(self._saved_page_states)
                for state in self._saved_page_states:
                    self.__dict__.update(state)
                    self.draw_page_decorations(num_pages)
                    super().showPage()
                super().save()

            def draw_page_decorations(self, total_pages):
                self.saveState()
                w, h = self._pagesize

                # 1. Subtle Diagonal Draft Watermark across every page
                self.saveState()
                self.setFont("Helvetica-Bold", 30)
                self.setFillColor(colors.HexColor("#f1f5f9"))
                self.translate(w / 2.0, h / 2.0)
                self.rotate(42)
                self.drawCentredString(0, 0, WATERMARK_DIAGONAL_TEXT)
                self.restoreState()

                # 2. Running Header (Page 2+)
                if self._pageNumber > 1:
                    self.saveState()
                    self.setFont("Helvetica", 7.5)
                    self.setFillColor(colors.HexColor("#64748b"))
                    self.drawString(54, h - 36, "CONVELINA Administrative Representation Draft")
                    self.drawRightString(w - 54, h - 36, f"Ref: {content_hash[:12]}...")
                    self.setStrokeColor(colors.HexColor("#e2e8f0"))
                    self.setLineWidth(0.5)
                    self.line(54, h - 42, w - 54, h - 42)
                    self.restoreState()

                # 3. Running Footer
                self.saveState()
                self.setFont("Helvetica", 7.5)
                self.setFillColor(colors.HexColor("#64748b"))
                self.drawString(54, 34, f"CONVELINA Resolution Platform • SHA-256: {content_hash[:16]}... • NOT AN OFFICIAL FORM")
                self.drawRightString(w - 54, 34, f"Page {self._pageNumber} of {total_pages}")
                self.setStrokeColor(colors.HexColor("#cbd5e1"))
                self.setLineWidth(0.5)
                self.line(54, 46, w - 54, 46)
                self.restoreState()

                self.restoreState()

        # Initialize Document Template with 0.75-inch (54pt) margins on A4
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54,
            title=title,
            author="CONVELINA Resolution Platform",
            subject="Administrative Representation Draft",
        )

        styles = getSampleStyleSheet()

        # Typography hierarchy
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName=bold_font_family,
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0f172a"),
            alignment=1,  # Center
            spaceAfter=6,
        )

        disclaimer_style = ParagraphStyle(
            "DisclaimerBanner",
            parent=styles["Normal"],
            fontName=font_family,
            fontSize=8,
            leading=11.5,
            textColor=colors.HexColor("#92400e"),  # Amber 800
            alignment=1,
            backColor=colors.HexColor("#fef3c7"),  # Amber 100
            borderColor=colors.HexColor("#fde68a"),
            borderWidth=1,
            borderPadding=6,
            spaceAfter=10,
        )

        section_heading_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Normal"],
            fontName=bold_font_family,
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=10,
            spaceAfter=4,
            keepWithNext=True,
        )

        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["Normal"],
            fontName=font_family,
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#334155"),
            spaceAfter=5,
        )

        bullet_style = ParagraphStyle(
            "DocBullet",
            parent=body_style,
            leftIndent=14,
            firstLineIndent=-10,
            spaceAfter=3,
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName=bold_font_family,
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#1e293b"),
        )

        table_cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName=font_family,
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#334155"),
        )

        story = []

        # 1. Mandatory Disclaimer Banner
        if language == "ta":
            disclaimer_text = "<b>அதிகாரப்பூர்வ அறிவிப்பு:</b> செயற்கை நுண்ணறிவு மூலம் உருவாக்கப்பட்ட நிர்வாக வரைவு — சமர்ப்பிக்கும் முன் அனைத்து விவரங்களையும் அதிகாரப்பூர்வ நடைமுறையையும் சரிபார்க்கவும்."
        elif language == "hi":
            disclaimer_text = "<b>सांविधिक सूचना:</b> एआई-जनरेटेड प्रशासनिक प्रारूप — प्रस्तुत करने से पहले सभी विवरणों और लागू आधिकारिक प्रक्रिया का सत्यापन करें।"
        elif language == "bilingual_en_ta":
            disclaimer_text = "<b>STATUTORY NOTICE / அதிகாரப்பூர்வ அறிவிப்பு:</b> AI-GENERATED ADMINISTRATIVE DRAFT — சமர்ப்பிக்கும் முன் அனைத்து விவரங்களையும் சரிபார்க்கவும்."
        else:
            disclaimer_text = f"<b>STATUTORY NOTICE:</b> {DRAFT_WATERMARK_TEXT}"

        story.append(Paragraph(disclaimer_text, disclaimer_style))
        story.append(Spacer(1, 4))

        # 2. Document Title
        story.append(Paragraph(f"<b>{title}</b>", title_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

        # 3. Process Content Lines
        lines = content.split("\n")
        i = 0
        table_rows = []
        in_table_section = False

        while i < len(lines):
            line = lines[i]
            trimmed = line.strip()

            if not trimmed:
                if table_rows:
                    # Flush table
                    t = Table(table_rows, colWidths=[150, 337])
                    t.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 6))
                    table_rows = []
                    in_table_section = False
                story.append(Spacer(1, 4))
                i += 1
                continue

            # Skip duplicate first-line disclaimers
            if "ai-generated" in trimmed.lower() and "review all" in trimmed.lower():
                i += 1
                continue

            # Heading Detection
            if (
                trimmed.startswith("### ")
                or trimmed.startswith("## ")
                or re.match(r"^\d+\.\s+[A-Z\u0B80-\u0BFF]", trimmed)
                or (trimmed.isupper() and len(trimmed) < 45 and not trimmed.startswith("["))
                or trimmed.startswith("PART ")
                or trimmed.startswith("பகுதி ")
            ):
                clean_heading = trimmed.lstrip("#").strip()
                story.append(Paragraph(f"<b>{clean_heading}</b>", section_heading_style))
                i += 1
                continue

            # Discrepancy Statement Structured Key-Value Pairs -> Table
            kv_match = re.match(r"^\s*-\s*([^:]+):\s*(.+)$", trimmed)
            if kv_match:
                k, v = kv_match.group(1).strip(), kv_match.group(2).strip()
                # Format bracketed placeholders in bold red
                v_formatted = re.sub(r"(\[[^\]]+\])", r"<font color='#dc2626'><b>\1</b></font>", v)
                table_rows.append([
                    Paragraph(f"<b>{k}</b>", table_header_style),
                    Paragraph(v_formatted, table_cell_style)
                ])
                i += 1
                continue

            # If we had table rows and current line isn't a KV pair, flush table
            if table_rows:
                t = Table(table_rows, colWidths=[150, 337])
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]))
                story.append(t)
                story.append(Spacer(1, 6))
                table_rows = []

            # Bulleted List
            if trimmed.startswith("- ") or trimmed.startswith("* ") or re.match(r"^\d+\.\s+", trimmed):
                bullet_item = re.sub(r"^[-*]\s+|\d+\.\s+", "", trimmed).strip()
                # Highlight placeholders
                formatted_bullet = re.sub(r"(\[[^\]]+\])", r"<font color='#dc2626'><b>\1</b></font>", bullet_item)
                story.append(Paragraph(f"&bull; {formatted_bullet}", bullet_style))
            else:
                formatted_line = re.sub(r"(\[[^\]]+\])", r"<font color='#dc2626'><b>\1</b></font>", trimmed)
                formatted_line = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", formatted_line)
                story.append(Paragraph(formatted_line, body_style))

            i += 1

        # Flush any trailing table
        if table_rows:
            t = Table(table_rows, colWidths=[150, 337])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(t)

        # 4. Build Document with NumberedCanvas
        doc.build(story, canvasmaker=NumberedCanvas)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    @staticmethod
    def export_docx(
        title: str,
        content: str,
        draft_id: Optional[str] = None,
        language: str = "en",
    ) -> bytes:
        """Generates a clean, Unicode-compatible DOCX with equivalent substantive content."""
        try:
            import docx
            from docx.shared import Inches, Pt, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.oxml import OxmlElement
            from docx.oxml.ns import qn
        except ImportError:
            raise RuntimeError("python-docx is required for DOCX export. Please install python-docx.")

        doc = docx.Document()

        # Compute content hash
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        # Detect script and set font family
        script = detect_text_script(content + " " + title)
        font_name = "Lohit Tamil" if script == "tamil" else "Segoe UI"

        # 0.75-inch margins on all sections
        for section in doc.sections:
            section.top_margin = Inches(0.75)
            section.bottom_margin = Inches(0.75)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)

            # Header
            header = section.header
            header_p = header.paragraphs[0]
            header_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            hrun = header_p.add_run("CONVELINA Administrative Representation Draft — Review Before Submission")
            hrun.font.name = "Segoe UI"
            hrun.font.size = Pt(8)
            hrun.font.color.rgb = RGBColor(148, 163, 184)

            # Footer
            footer = section.footer
            footer_p = footer.paragraphs[0]
            footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            frun = footer_p.add_run(f"CONVELINA Resolution Platform • SHA-256: {content_hash[:16]}... • NOT AN OFFICIAL FORM")
            frun.font.name = "Segoe UI"
            frun.font.size = Pt(8)
            frun.font.color.rgb = RGBColor(148, 163, 184)

        # 1. Statutory Notice Banner
        if language == "ta":
            banner_text = "அதிகாரப்பூர்வ அறிவிப்பு: செயற்கை நுண்ணறிவு மூலம் உருவாக்கப்பட்ட நிர்வாக வரைவு — சமர்ப்பிக்கும் முன் அனைத்து விவரங்களையும் அதிகாரப்பூர்வ நடைமுறையையும் சரிபார்க்கவும்."
        elif language == "hi":
            banner_text = "सांविधिक सूचना: एआई-जनरेटेड प्रशासनिक प्रारूप — प्रस्तुत करने से पहले सभी विवरणों और लागू आधिकारिक प्रक्रिया का सत्यापन करें।"
        elif language == "bilingual_en_ta":
            banner_text = "STATUTORY NOTICE / அதிகாரப்பூர்வ அறிவிப்பு: AI-GENERATED ADMINISTRATIVE DRAFT — சமர்ப்பிக்கும் முன் அனைத்து விவரங்களையும் சரிபார்க்கவும்."
        else:
            banner_text = f"STATUTORY NOTICE: {DRAFT_WATERMARK_TEXT}"

        banner_p = doc.add_paragraph()
        banner_run = banner_p.add_run(banner_text)
        banner_run.bold = True
        banner_run.font.name = font_name
        banner_run.font.size = Pt(8.5)
        banner_run.font.color.rgb = RGBColor(180, 83, 9)  # Amber 700
        banner_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        banner_p.paragraph_format.space_after = Pt(10)

        # 2. Document Title
        title_p = doc.add_paragraph()
        title_run = title_p.add_run(title)
        title_run.bold = True
        title_run.font.name = font_name
        title_run.font.size = Pt(15)
        title_run.font.color.rgb = RGBColor(15, 23, 42)
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_p.paragraph_format.space_after = Pt(12)

        # 3. Substantive Content Processing
        lines = content.split("\n")
        table_rows = []

        def flush_docx_table():
            nonlocal table_rows
            if not table_rows:
                return
            tbl = doc.add_table(rows=len(table_rows), cols=2)
            tbl.style = "Table Grid"
            for r_idx, (col1, col2) in enumerate(table_rows):
                row = tbl.rows[r_idx]
                # Col 1
                c1 = row.cells[0]
                c1.width = Inches(2.2)
                p1 = c1.paragraphs[0]
                p1.paragraph_format.space_after = Pt(2)
                r1 = p1.add_run(col1)
                r1.bold = True
                r1.font.name = font_name
                r1.font.size = Pt(9)
                r1.font.color.rgb = RGBColor(30, 41, 59)
                # Col 2
                c2 = row.cells[1]
                c2.width = Inches(4.5)
                p2 = c2.paragraphs[0]
                p2.paragraph_format.space_after = Pt(2)
                _add_docx_formatted_runs(p2, col2, font_name)
            doc.add_paragraph().paragraph_format.space_after = Pt(4)
            table_rows = []

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                flush_docx_table()
                continue

            if "ai-generated" in trimmed.lower() and "review all" in trimmed.lower():
                continue

            # Heading Detection
            if (
                trimmed.startswith("### ")
                or trimmed.startswith("## ")
                or re.match(r"^\d+\.\s+[A-Z\u0B80-\u0BFF]", trimmed)
                or (trimmed.isupper() and len(trimmed) < 45 and not trimmed.startswith("["))
                or trimmed.startswith("PART ")
                or trimmed.startswith("பகுதி ")
            ):
                flush_docx_table()
                clean_heading = trimmed.lstrip("#").strip()
                h = doc.add_heading(level=2)
                h_run = h.add_run(clean_heading)
                h_run.bold = True
                h_run.font.name = font_name
                h_run.font.size = Pt(11)
                h_run.font.color.rgb = RGBColor(15, 23, 42)
                h.paragraph_format.space_before = Pt(8)
                h.paragraph_format.space_after = Pt(3)
                continue

            # Structured Discrepancy Key-Value Pair
            kv_match = re.match(r"^\s*-\s*([^:]+):\s*(.+)$", trimmed)
            if kv_match:
                table_rows.append((kv_match.group(1).strip(), kv_match.group(2).strip()))
                continue

            flush_docx_table()

            # Bulleted List
            if trimmed.startswith("- ") or trimmed.startswith("* ") or re.match(r"^\d+\.\s+", trimmed):
                bullet_item = re.sub(r"^[-*]\s+|\d+\.\s+", "", trimmed).strip()
                bp = doc.add_paragraph(style="List Bullet")
                bp.paragraph_format.space_after = Pt(2)
                _add_docx_formatted_runs(bp, bullet_item, font_name)
            else:
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(3.5)
                _add_docx_formatted_runs(p, trimmed, font_name)

        flush_docx_table()

        buffer = io.BytesIO()
        doc.save(buffer)
        docx_bytes = buffer.getvalue()
        buffer.close()
        return docx_bytes


def _add_docx_formatted_runs(paragraph, text: str, font_name: str = "Segoe UI"):
    """Adds styled runs to paragraph, highlighting bracketed placeholders [Placeholder] in red bold."""
    from docx.shared import Pt, RGBColor
    pattern = re.compile(r"(\[[^\]]+\])")
    parts = pattern.split(text)
    for part in parts:
        if not part:
            continue
        run = paragraph.add_run(part)
        run.font.name = font_name
        if part.startswith("[") and part.endswith("]"):
            run.bold = True
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(220, 38, 38)  # Red 600
        else:
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(51, 65, 85)
