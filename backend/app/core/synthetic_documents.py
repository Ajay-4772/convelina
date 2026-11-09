"""
CONVELINA — Synthetic Document & Placeholder Asset Generator
Generates readable, properly formatted synthetic sample documents (PDF and PNG)
for all six supported document categories:
1. Aadhaar Card
2. PAN Card
3. Passport
4. Class 10 Certificate
5. Class 12 Certificate
6. EPF/UAN Records

Strict Compliance:
- Prints 'SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM'.
- Uses 100% fictional test data. Never uses real personal identity information.
- Does NOT reproduce official government seals, signatures, QR codes, or security features.
- Enables end-to-end testing of PDF preview, download, OCR extraction, field confidence, and conflict detection.
"""

import io
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PIL import Image, ImageDraw, ImageFont


SYNTHETIC_DATA_PROFILES = {
    "aadhaar": {
        "title": "Aadhaar Card Sample Document",
        "category_name": "Aadhaar Identity Record",
        "authority": "Sample Registration Authority (Fictional)",
        "fields": {
            "full_name": "Rajesh Kumar",
            "date_of_birth": "12/04/1991",
            "gender": "Male",
            "aadhaar_number": "9876 5432 1098",
            "masked_aadhaar": "XXXX-XXXX-1098",
            "address": "42, Shanti Vihar, Ring Road, New Delhi",
            "pincode": "110001",
        }
    },
    "pan": {
        "title": "Permanent Account Number (PAN) Card Sample",
        "category_name": "Income Tax Department Record (Fictional)",
        "authority": "Sample Tax Assessment Authority",
        "fields": {
            "full_name": "RAJESH KUMAR",
            "father_name": "SURESH KUMAR",
            "date_of_birth": "12/04/1991",
            "pan_number": "ABCDE1234F",
            "masked_pan": "AB***1234F",
        }
    },
    "passport": {
        "title": "Passport Particulars Sample Page",
        "category_name": "Travel & Nationality Document",
        "authority": "Sample Consular Office (Fictional)",
        "fields": {
            "surname": "KUMAR",
            "given_name": "RAJESH",
            "full_name": "RAJESH KUMAR",
            "passport_number": "Z1234567",
            "nationality": "INDIAN",
            "date_of_birth": "12/04/1991",
            "place_of_birth": "NEW DELHI",
            "gender": "Male",
            "date_of_issue": "15/01/2020",
            "date_of_expiry": "14/01/2030",
            "father_name": "SURESH KUMAR",
            "mother_name": "SUNITA KUMAR",
            "address": "42 Shanti Vihar, Ring Road, New Delhi - 110001",
        }
    },
    "education_10th": {
        "title": "Secondary School Examination (Class X) Certificate",
        "category_name": "Educational Record (Class 10)",
        "authority": "Central Board of Secondary Education (CBSE Sample)",
        "fields": {
            "full_name": "RAJESH KUMAR",
            "father_name": "SURESH KUMAR",
            "mother_name": "SUNITA KUMAR",
            "date_of_birth": "12/04/1991",
            "roll_number": "6124589",
            "registration_number": "R/2007/6124",
            "board": "CBSE",
            "examination_year": "2007",
            "result": "PASSED",
        }
    },
    "education_12th": {
        "title": "Senior School Certificate Examination (Class XII)",
        "category_name": "Educational Record (Class 12)",
        "authority": "Central Board of Secondary Education (CBSE Sample)",
        "fields": {
            "full_name": "RAJESH KUMAR",
            "father_name": "SURESH KUMAR",
            "mother_name": "SUNITA KUMAR",
            "date_of_birth": "12/04/1991",
            "roll_number": "8245190",
            "registration_number": "R/2009/8245",
            "board": "CBSE",
            "examination_year": "2009",
            "result": "PASSED",
        }
    },
    "epf": {
        "title": "Employees' Provident Fund Member Record / Passbook",
        "category_name": "EPF / UAN Record",
        "authority": "Employees' Provident Fund Organisation (Fictional Sample)",
        "fields": {
            "full_name": "RAJESH KUMAR",
            "uan": "100987654321",
            "masked_uan": "UAN-1009****4321",
            "member_id": "DLCPM00123450000123456",
            "establishment_name": "ACME TECH CONSULTING SERVICES PVT LTD",
            "establishment_id": "DLCPM0012345",
            "date_of_birth": "12/04/1991",
            "date_of_joining": "01/06/2014",
            "date_of_exit": None,
        }
    }
}


def generate_synthetic_document_pdf(
    category: str,
    variant: str = "standard",
    custom_fields: Optional[Dict[str, Any]] = None
) -> bytes:
    """
    Generates a readable synthetic PDF document for one of the six categories.
    """
    cat_key = category.lower()
    if cat_key not in SYNTHETIC_DATA_PROFILES:
        cat_key = "aadhaar"

    profile = SYNTHETIC_DATA_PROFILES[cat_key]
    fields = dict(profile["fields"])
    if custom_fields:
        fields.update(custom_fields)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
        title=f"{profile['title']} (Synthetic)",
        author="CONVELINA Test Harness",
        subject="SYNTHETIC_TEST_ASSET",
        keywords="SYNTHETIC_TEST_ASSET, FICTIONAL, DEVELOPMENT_ONLY",
    )

    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        "SynHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        alignment=1,
        textColor=colors.HexColor("#1F1E1D")
    )
    auth_style = ParagraphStyle(
        "SynAuth",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        alignment=1,
        textColor=colors.HexColor("#555555")
    )
    banner_style = ParagraphStyle(
        "SynBanner",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        alignment=1,
        textColor=colors.HexColor("#BA1A1A")
    )
    banner_sub = ParagraphStyle(
        "SynBannerSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        alignment=1,
        textColor=colors.HexColor("#7F1D1D")
    )
    field_lbl = ParagraphStyle(
        "SynFieldLbl",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#333333")
    )
    field_val = ParagraphStyle(
        "SynFieldVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#111111")
    )

    story = []

    # 1. Prominent Synthetic Development Disclaimer Banner
    banner_table = [
        [
            Paragraph("<b>⚠️ SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM</b>", banner_style)
        ],
        [
            Paragraph(
                "Fictional test asset generated for platform development, OCR extraction, and preview testing. "
                "Contains NO authentic government seals, signatures, or security features. "
                "All names, numbers, and identifiers are completely fictional.",
                banner_sub
            )
        ]
    ]
    tb = Table(banner_table, colWidths=[540])
    tb.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FCE8E6")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#F5C2C7")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(tb)
    story.append(Spacer(1, 12))

    # 2. Document Title and Authority
    story.append(Paragraph(profile["authority"], auth_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(profile["title"], header_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Category: <b>{profile['category_name']}</b> | Test Variant: <i>{variant.capitalize()}</i>", auth_style))
    story.append(Spacer(1, 14))

    # 3. Structured Fields Table (Readable for humans and OCR)
    rows = []
    field_items = list(fields.items())

    # Build 2-column or 4-column table
    for i in range(0, len(field_items), 2):
        k1, v1 = field_items[i]
        label1 = k1.replace("_", " ").title()
        val1 = str(v1) if v1 is not None else "Not Specified"

        if i + 1 < len(field_items):
            k2, v2 = field_items[i+1]
            label2 = k2.replace("_", " ").title()
            val2 = str(v2) if v2 is not None else "Not Specified"
            rows.append([
                Paragraph(f"<b>{label1}:</b>", field_lbl),
                Paragraph(val1, field_val),
                Paragraph(f"<b>{label2}:</b>", field_lbl),
                Paragraph(val2, field_val),
            ])
        else:
            rows.append([
                Paragraph(f"<b>{label1}:</b>", field_lbl),
                Paragraph(val1, field_val),
                Paragraph("", field_lbl),
                Paragraph("", field_val),
            ])

    table = Table(rows, colWidths=[110, 160, 110, 160])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FAF9F5")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#D8D7D2")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#EAE9E4")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 14))

    # 4. Instructions and Verification Footer
    footer_text = Paragraph(
        "<b>Instructions for Verification:</b> This document contains machine-readable key-value pairs formatted "
        "to validate OCR confidence scoring, field parsing heuristics, and cross-document discrepancy detection engines. "
        "Reported values must be confirmed by the citizen prior to final comparison.",
        field_val
    )
    story.append(footer_text)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC")))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "CONVELINA SECURE TEST HARNESS • PROVENANCE: SYNTHETIC_TEST_ASSET • ZERO REAL PII",
        auth_style
    ))

    doc.build(story)
    return buffer.getvalue()


def _get_font(size: int, is_tamil: bool = False) -> ImageFont.ImageFont:
    import os
    candidate_paths = [
        "/usr/share/fonts/truetype/lohit-tamil/Lohit-Tamil.ttf" if is_tamil else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/lohit-tamil/Lohit-Tamil.ttf",
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def generate_synthetic_document_image(
    category: str,
    variant: str = "standard",
    custom_fields: Optional[Dict[str, Any]] = None,
    width: int = 800,
    height: int = 500
) -> bytes:
    """
    Generates a clean synthetic PNG image for one of the six categories.
    """
    cat_key = category.lower()
    if cat_key not in SYNTHETIC_DATA_PROFILES:
        cat_key = "aadhaar"

    profile = SYNTHETIC_DATA_PROFILES[cat_key]
    fields = dict(profile["fields"])
    if custom_fields:
        fields.update(custom_fields)

    bg_color = (255, 255, 255) if variant != "low_confidence" else (230, 230, 230)
    text_color = (20, 20, 20) if variant != "low_confidence" else (140, 140, 140)

    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    scale = max(0.5, width / 800.0)
    font_banner = _get_font(max(10, int(11 * scale)))
    font_auth = _get_font(max(10, int(11 * scale)))
    font_title = _get_font(max(12, int(14 * scale)))
    font_label = _get_font(max(10, int(11 * scale)))
    font_val = _get_font(max(10, int(11 * scale)))
    font_tamil = _get_font(max(11, int(12 * scale)), is_tamil=True)
    font_footer = _get_font(max(9, int(10 * scale)))

    # Outer border
    draw.rectangle([(10, 10), (width - 10, height - 10)], outline=(200, 200, 200), width=2)

    # Red Disclaimer Banner
    banner_h = int(50 * scale)
    draw.rectangle([(12, 12), (width - 12, max(40, banner_h))], fill=(252, 232, 230))
    draw.text((int(25 * scale), int(20 * scale)), "SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM", fill=(186, 26, 26), font=font_banner)

    # Header
    draw.text((int(25 * scale), int(60 * scale)), profile["authority"], fill=(100, 100, 100), font=font_auth)
    draw.text((int(25 * scale), int(80 * scale)), profile["title"].upper(), fill=(20, 20, 20), font=font_title)
    draw.line([(int(25 * scale), int(105 * scale)), (width - int(25 * scale), int(105 * scale))], fill=(220, 220, 220), width=1)

    # Fields
    y = int(125 * scale)
    y_step = int(28 * scale)
    x_val = int(240 * scale)

    for k, v in fields.items():
        if v is None:
            continue
        label = k.replace("_", " ").title() + ":"
        val_str = str(v)
        has_tamil = any('\u0B80' <= c <= '\u0BFF' for c in val_str)
        v_font = font_tamil if has_tamil else font_val

        draw.text((int(35 * scale), y), label, fill=(80, 80, 80), font=font_label)
        draw.text((x_val, y), val_str, fill=text_color, font=v_font)
        y += y_step
        if y > height - int(60 * scale):
            break

    # Footer
    draw.line([(int(25 * scale), height - int(40 * scale)), (width - int(25 * scale), height - int(40 * scale))], fill=(220, 220, 220), width=1)
    draw.text((int(25 * scale), height - int(30 * scale)), "CONVELINA TEST ASSET • PROVENANCE: SYNTHETIC_TEST_ASSET", fill=(130, 130, 130), font=font_footer)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
