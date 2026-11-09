import hashlib
import os
import uuid
import logging
from typing import Tuple, Optional
from app.config import settings

logger = logging.getLogger("consolith.storage")

def ensure_temp_dir() -> str:
    """
    Ensures the temporary storage directory exists and returns its absolute path.
    """
    temp_dir = os.path.abspath(settings.STORAGE_TEMP_DIR)
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def ensure_official_forms_dir() -> str:
    """
    Ensures the official repository assets directory exists and returns its absolute path.
    Falls back gracefully if running in a non-containerized local environment.
    """
    configured_dir = settings.STORAGE_OFFICIAL_FORMS_DIR
    try:
        abs_dir = os.path.abspath(configured_dir)
        os.makedirs(abs_dir, exist_ok=True)
        return abs_dir
    except (OSError, PermissionError):
        # Fallback to local directory inside backend root
        fallback_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "official_forms"))
        os.makedirs(fallback_dir, exist_ok=True)
        return fallback_dir

def compute_sha256(content: bytes) -> str:
    """
    Calculates SHA-256 cryptographic hash of byte content.
    """
    return hashlib.sha256(content).hexdigest()

def save_temp_document(content: bytes, ext: str) -> Tuple[str, str]:
    """
    Saves file bytes to an unpredictable server-side filename in the temporary storage dir.
    Returns (absolute_file_path, sha256_hash).
    """
    temp_dir = ensure_temp_dir()
    unique_filename = f"doc_{uuid.uuid4().hex}{ext}"
    target_path = os.path.join(temp_dir, unique_filename)
    
    with open(target_path, "wb") as f:
        f.write(content)
        
    file_hash = compute_sha256(content)
    logger.info("Saved temporary document to disk (sha256=%s...)", file_hash[:12])
    return target_path, file_hash

def delete_temp_document(file_path: str) -> bool:
    """
    Safely deletes a temporary file from disk.
    Ensures path lies strictly within the configured temporary storage directory.
    """
    if not file_path or not os.path.exists(file_path):
        return False
        
    temp_dir = ensure_temp_dir()
    abs_target = os.path.abspath(file_path)
    
    # Path traversal safety check
    if not abs_target.startswith(temp_dir):
        logger.warning("Attempted deletion of file outside temporary storage: %s", abs_target)
        return False
        
    try:
        os.remove(abs_target)
        logger.info("Successfully deleted temporary file: %s", abs_target)
        return True
    except OSError as e:
        logger.error("Failed to delete temporary file %s: %s", abs_target, str(e))
        return False

# ===========================================================================
# Official Forms Repository Asset Storage (Phase P3D)
# ===========================================================================

def get_official_form_path(form_id_or_storage_ref: str) -> Optional[str]:
    """
    Resolves and validates the absolute path to an official form asset.
    Strictly prevents path traversal attacks:
    - Normalizes path
    - Ensures path resides inside the official forms storage directory
    - Rejects any null bytes or directory traversal characters ('..', '~')
    """
    if not form_id_or_storage_ref:
        return None

    # Sanitize against path traversal tricks
    if "\x00" in form_id_or_storage_ref or ".." in form_id_or_storage_ref:
        logger.warning("Path traversal attempt detected in official form ref: %s", form_id_or_storage_ref)
        return None

    forms_dir = ensure_official_forms_dir()
    
    # Check if form_id directly maps to a filename
    candidate = form_id_or_storage_ref
    if not candidate.endswith(".pdf"):
        candidate = f"{candidate}.pdf"

    # If it is a full or relative path, take basename for strict containment
    safe_filename = os.path.basename(candidate)
    target_path = os.path.abspath(os.path.join(forms_dir, safe_filename))

    if not target_path.startswith(forms_dir):
        logger.warning("Resolved path escapes official forms directory: %s", target_path)
        return None

    if not os.path.isfile(target_path):
        return None

    return target_path

def save_official_form_asset(form_id: str, content: bytes, filename: Optional[str] = None) -> Tuple[str, str, int]:
    """
    Saves an official form asset into the official repository storage.
    Computes cryptographic SHA-256 hash and records size.
    Returns (relative_storage_path, sha256_hash, file_size_bytes).
    """
    forms_dir = ensure_official_forms_dir()
    safe_name = os.path.basename(filename) if filename else f"{form_id}.pdf"
    if not safe_name.endswith(".pdf"):
        safe_name = f"{form_id}.pdf"

    target_path = os.path.join(forms_dir, safe_name)
    with open(target_path, "wb") as f:
        f.write(content)

    sha256_hash = compute_sha256(content)
    file_size_bytes = len(content)
    logger.info("Saved official form asset %s (%d bytes, sha256=%s...)", safe_name, file_size_bytes, sha256_hash[:12])
    return safe_name, sha256_hash, file_size_bytes

def generate_default_official_form_pdf(form_dict: dict) -> bytes:
    """
    Generates a readable synthetic placeholder PDF document for development and testing using ReportLab.
    Clearly marks document as 'SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM'.
    Includes issuing authority, category, purpose, instructions, and fictional example fields.
    Does not reproduce official government seals, signatures, QR codes, or security features.
    """
    import io
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "FormTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        alignment=1,
        textColor=colors.HexColor("#1F1E1D")
    )
    authority_style = ParagraphStyle(
        "Authority",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        alignment=1,
        textColor=colors.HexColor("#73726E")
    )
    synthetic_banner_style = ParagraphStyle(
        "SyntheticBanner",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        alignment=1,
        textColor=colors.HexColor("#BA1A1A")
    )
    synthetic_sub_style = ParagraphStyle(
        "SyntheticSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        alignment=1,
        textColor=colors.HexColor("#7F1D1D")
    )
    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#C96442")
    )
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1F1E1D")
    )

    story = []

    # 1. Prominent Synthetic Development Disclaimer Banner
    banner_table = [
        [
            Paragraph("<b>⚠️ SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM</b>", synthetic_banner_style)
        ],
        [
            Paragraph(
                "Fictional test asset generated for platform development, OCR extraction testing, and preview validation. "
                "Does NOT contain authentic official government seals, digital signatures, holograms, or QR codes. "
                "Download authentic official originals directly from the issuing authority portal.",
                synthetic_sub_style
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
    story.append(Spacer(1, 10))

    # 2. Header
    story.append(Paragraph(form_dict.get("issuing_authority", "Government Authority"), authority_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(form_dict.get("form_name", "Statutory Form"), title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Form Identifier: <b>{form_dict.get('form_id', '')}</b> | Version: {form_dict.get('version', '1.0')} | Language: {form_dict.get('language', 'en').upper()} | Provenance: <b>SYNTHETIC_TEST_ASSET</b>", authority_style))
    story.append(Spacer(1, 12))

    # Purpose & Category
    meta_table = [
        [
            Paragraph("<b>Document Category:</b>", body_style),
            Paragraph(form_dict.get("document_category", "").upper(), body_style),
            Paragraph("<b>Verification Status:</b>", body_style),
            Paragraph(form_dict.get("verification_status", "verified").upper(), body_style)
        ],
        [
            Paragraph("<b>Statutory Purpose:</b>", body_style),
            Paragraph(form_dict.get("purpose", ""), body_style),
            Paragraph("<b>Official Portal:</b>", body_style),
            Paragraph(form_dict.get("official_download_url", ""), body_style)
        ]
    ]
    t = Table(meta_table, colWidths=[110, 160, 110, 160])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FAF9F5")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E5E0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E5E0")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # Applicable Issues & Conditions
    story.append(Paragraph("1. APPLICABILITY & MANDATORY PREREQUISITES", section_style))
    story.append(Spacer(1, 6))
    conditions = form_dict.get("applicable_conditions", [])
    if conditions:
        for c in conditions:
            story.append(Paragraph(f"• {c}", body_style))
            story.append(Spacer(1, 2))
    else:
        story.append(Paragraph("• Standard statutory verification rules apply. Carry original proof documents.", body_style))
    story.append(Spacer(1, 12))

    # Standard Application Fields Placeholder
    story.append(Paragraph("2. APPLICANT PARTICULARS (CORRECTION / UPDATE REQUEST)", section_style))
    story.append(Spacer(1, 6))

    fields_data = [
        [Paragraph("<b>Field Name</b>", body_style), Paragraph("<b>Existing Recorded Value</b>", body_style), Paragraph("<b>Correct Value Requested</b>", body_style)],
        [Paragraph("Applicant Full Name", body_style), Paragraph("", body_style), Paragraph("", body_style)],
        [Paragraph("Date of Birth (DD/MM/YYYY)", body_style), Paragraph("", body_style), Paragraph("", body_style)],
        [Paragraph("Father's / Parent's Name", body_style), Paragraph("", body_style), Paragraph("", body_style)],
        [Paragraph("Proof Document Enclosed", body_style), Paragraph("", body_style), Paragraph("", body_style)],
    ]
    fields_table = Table(fields_data, colWidths=[160, 190, 190])
    fields_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EBE9E4")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E5E0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E5E0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(fields_table)
    story.append(Spacer(1, 16))

    # Declaration & Signature Block
    story.append(Paragraph("3. STATUTORY DECLARATION", section_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "I hereby solemnly affirm and declare that the information provided above is true and correct to the best of my knowledge and belief. "
        "I understand that providing false information or forged documents is a punishable statutory offense under the applicable Acts of the Republic of India.",
        body_style
    ))
    story.append(Spacer(1, 28))

    sig_data = [
        [Paragraph("Date: ________________________", body_style), Paragraph("Signature / Thumb Impression of Applicant: ________________________", body_style)],
        [Paragraph("Place: _______________________", body_style), Paragraph("Authorized Stamp / Seal (if applicable): ________________________", body_style)]
    ]
    sig_table = Table(sig_data, colWidths=[200, 340])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 16))

    # Legal Disclaimer
    story.append(Paragraph(
        "<b>Notice:</b> Verified statutory format cataloged in CONVELINA. Issued for citizen reconciliation assistance.",
        authority_style
    ))

    doc.build(story)
    return buffer.getvalue()


# ===========================================================================
# Multimodal In-Chat Temporary Attachments Storage (Phase P3E)
# ===========================================================================

def ensure_temp_attachments_dir() -> str:
    """
    Ensures the temporary chat attachments directory exists and returns its absolute path.
    """
    configured_dir = getattr(settings, "STORAGE_TEMP_ATTACHMENTS_DIR", "/tmp/consolith/temp_attachments")
    abs_dir = os.path.abspath(configured_dir)
    os.makedirs(abs_dir, exist_ok=True)
    return abs_dir

def save_temp_attachment(content: bytes, ext: str, user_id: Optional[str] = None) -> Tuple[str, str]:
    """
    Saves temporary chat attachment bytes to an unpredictable server-side filename.
    Returns (absolute_file_path, sha256_hash).
    """
    attachments_dir = ensure_temp_attachments_dir()
    unique_filename = f"att_{uuid.uuid4().hex}{ext}"
    target_path = os.path.join(attachments_dir, unique_filename)

    with open(target_path, "wb") as f:
        f.write(content)

    file_hash = compute_sha256(content)
    logger.info("Saved temporary chat attachment to disk: %s (sha256=%s...)", unique_filename, file_hash[:12])
    return target_path, file_hash

def get_temp_attachment_path(storage_ref: str) -> Optional[str]:
    """
    Resolves and validates the absolute path to a temporary chat attachment.
    Strictly prevents path traversal attacks:
    - Normalizes path
    - Ensures path resides inside the attachments directory
    - Rejects any null bytes or directory traversal characters ('..', '~')
    """
    if not storage_ref:
        return None

    if "\x00" in storage_ref or ".." in storage_ref or "~" in storage_ref:
        logger.warning("Path traversal attempt detected in attachment storage_ref: %s", storage_ref)
        return None

    attachments_dir = ensure_temp_attachments_dir()
    
    # If storage_ref is just a filename
    if not os.path.isabs(storage_ref):
        target = os.path.join(attachments_dir, os.path.basename(storage_ref))
    else:
        target = os.path.abspath(storage_ref)

    if not target.startswith(attachments_dir):
        logger.warning("Attempted attachment path traversal outside temp directory: %s", target)
        return None

    if not os.path.exists(target):
        return None

    return target

def delete_temp_attachment(file_path: str) -> bool:
    """
    Safely deletes a temporary attachment file from disk.
    Guarantees path lies strictly within the configured temporary attachments directory.
    """
    if not file_path:
        return False

    attachments_dir = ensure_temp_attachments_dir()
    abs_target = os.path.abspath(file_path)

    if not abs_target.startswith(attachments_dir):
        logger.warning("Attempted deletion of file outside temp attachments directory: %s", abs_target)
        return False

    if not os.path.exists(abs_target):
        return False

    try:
        os.remove(abs_target)
        logger.info("Successfully deleted temporary attachment file: %s", abs_target)
        return True
    except OSError as e:
        logger.error("Failed to delete temporary attachment file %s: %s", abs_target, str(e))
        return False

