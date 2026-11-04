"""CONVELINA - Module 7 Document Exporter Service

Exports correction drafts into clean, professional PDF and DOCX files.
Features:
- ReportLab for PDF: Clean margins, headers, prominent draft notices, signature blocks.
- python-docx for DOCX: Standard heading styles, bullet points, disclaimer banner.
- Zero fake government logos, emblems, seals, or fabricated approval stamps.
"""

import io
import re
from typing import Optional

DRAFT_WATERMARK_TEXT = (
    "AI-GENERATED DRAFT — REVIEW ALL INFORMATION BEFORE SUBMISSION"
)


class DocumentExporter:
    """Exports structured plain-text / markdown correction drafts into PDF and DOCX format."""

    @staticmethod
    def export_pdf(title: str, content: str, draft_id: Optional[str] = None) -> bytes:
        """Generates a professionally formatted PDF document from draft content."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
        except ImportError:
            raise RuntimeError("ReportLab is required for PDF export. Please install reportlab.")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#1e293b"),  # Slate 800
            alignment=1,  # Center
            spaceAfter=8,
        )

        notice_style = ParagraphStyle(
            "NoticeStyle",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#b45309"),  # Amber 700
            alignment=1,
            backColor=colors.HexColor("#fef3c7"),  # Amber 100
            borderPadding=4,
            spaceAfter=12,
        )

        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6,
        )

        heading_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=8,
            spaceAfter=4,
        )

        story = []

        # Draft Banner
        story.append(Paragraph(f"<b>NOTICE:</b> {DRAFT_WATERMARK_TEXT}", notice_style))
        story.append(Spacer(1, 6))

        # Title
        story.append(Paragraph(title, title_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=12))

        # Process lines
        lines = content.split("\n")
        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                story.append(Spacer(1, 6))
                continue

            # Skip duplicate notice if it matches the first line
            if "AI-generated draft" in trimmed and "review all information" in trimmed.lower():
                continue

            # Heading detection
            if trimmed.startswith("### ") or trimmed.startswith("## ") or (trimmed.isupper() and len(trimmed) < 40 and not trimmed.startswith("[")):
                clean_heading = trimmed.lstrip("#").strip()
                story.append(Paragraph(f"<b>{clean_heading}</b>", heading_style))
            elif trimmed.startswith("- ") or trimmed.startswith("* "):
                bullet_item = trimmed[2:].strip()
                # Highlight placeholders in bold red/amber
                formatted_bullet = re.sub(r"(\[[^\]]+\])", r"<font color='#dc2626'><b>\1</b></font>", bullet_item)
                story.append(Paragraph(f"&bull; {formatted_bullet}", body_style))
            else:
                formatted_line = re.sub(r"(\[[^\]]+\])", r"<font color='#dc2626'><b>\1</b></font>", trimmed)
                # Convert basic markdown bold **text**
                formatted_line = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", formatted_line)
                story.append(Paragraph(formatted_line, body_style))

        # Footer space
        story.append(Spacer(1, 16))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceAfter=6))
        footer_text = f"CONVELINA Operations & Resolution Platform | Generated Draft Document"
        story.append(Paragraph(footer_text, ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#94a3b8"), alignment=1)))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    @staticmethod
    def export_docx(title: str, content: str, draft_id: Optional[str] = None) -> bytes:
        """Generates a clean DOCX document from draft content."""
        try:
            import docx
            from docx.shared import Inches, Pt, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH
        except ImportError:
            raise RuntimeError("python-docx is required for DOCX export. Please install python-docx.")

        doc = docx.Document()

        # Set page margins to 1 inch
        for section in doc.sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)

        # Draft Banner
        banner_p = doc.add_paragraph()
        banner_run = banner_p.add_run(f"NOTICE: {DRAFT_WATERMARK_TEXT}")
        banner_run.bold = True
        banner_run.font.size = Pt(8.5)
        banner_run.font.color.rgb = RGBColor(180, 83, 9)  # Amber 700
        banner_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Title
        title_p = doc.add_paragraph()
        title_run = title_p.add_run(title)
        title_run.bold = True
        title_run.font.size = Pt(16)
        title_run.font.color.rgb = RGBColor(15, 23, 42)
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Content
        lines = content.split("\n")
        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue

            if "AI-generated draft" in trimmed and "review all information" in trimmed.lower():
                continue

            if trimmed.startswith("### ") or trimmed.startswith("## "):
                clean_heading = trimmed.lstrip("#").strip()
                h = doc.add_heading(clean_heading, level=2)
                h.paragraph_format.space_before = Pt(8)
                h.paragraph_format.space_after = Pt(4)
            elif trimmed.startswith("- ") or trimmed.startswith("* "):
                bullet_item = trimmed[2:].strip()
                bp = doc.add_paragraph(style="List Bullet")
                _add_formatted_runs(bp, bullet_item)
            else:
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(4)
                _add_formatted_runs(p, trimmed)

        # Footer notice
        doc.add_paragraph()
        footer_p = doc.add_paragraph()
        footer_run = footer_p.add_run("CONVELINA Operations & Resolution Platform — Self-Service Draft")
        footer_run.font.size = Pt(8)
        footer_run.font.color.rgb = RGBColor(148, 163, 184)
        footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        buffer = io.BytesIO()
        doc.save(buffer)
        docx_bytes = buffer.getvalue()
        buffer.close()
        return docx_bytes


def _add_formatted_runs(paragraph, text: str):
    """Helper to highlight bracketed placeholders [Placeholder] in red bold."""
    from docx.shared import Pt, RGBColor
    pattern = re.compile(r"(\[[^\]]+\])")
    parts = pattern.split(text)
    for part in parts:
        if not part:
            continue
        run = paragraph.add_run(part)
        if part.startswith("[") and part.endswith("]"):
            run.bold = True
            run.font.color.rgb = RGBColor(220, 38, 38)  # Red 600
        else:
            run.font.size = Pt(10.5)
            run.font.color.rgb = RGBColor(51, 65, 85)
