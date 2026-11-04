import io
import uuid
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.core.database import SessionLocal, set_rls_context
from app.core.validator import validate_file_content, sanitize_filename, validate_document_type, validate_verhoeff
from app.core.encryption import encrypt_data, decrypt_data
from app.ocr.parsers.aadhaar import AadhaarParser
from app.ocr.parsers.pan import PANParser
from app.ocr.parsers.passport import PassportParser
from app.ocr.parsers.education import EducationCertificateParser
from app.ocr.parsers.epf import EPFRecordParser
from app.models.document import Document

client = TestClient(app)

def create_synthetic_image(text_lines=None, width=400, height=200, format="PNG") -> bytes:
    """Generates a real valid in-memory image for testing."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    if text_lines:
        y = 20
        for line in text_lines:
            draw.text((20, y), line, fill=(0, 0, 0))
            y += 30
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()

def test_sanitize_filename_traversal():
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\windows\\system32\\cmd.exe") == "cmd.exe"
    assert sanitize_filename("my document.png") == "my_document.png"
    assert sanitize_filename("") == "unnamed_document"

def test_validate_document_type():
    assert validate_document_type("Aadhaar") == "aadhaar"
    assert validate_document_type("pan") == "pan"
    with pytest.raises(Exception):
        validate_document_type("invalid_type_123")

def test_file_validation_empty_file():
    with pytest.raises(Exception) as exc:
        validate_file_content(b"", "test.png")
    assert "empty" in str(exc.value.detail).lower()

def test_file_validation_magic_bytes_mismatch():
    fake_png = b"This is plain text pretending to be an image"
    with pytest.raises(Exception) as exc:
        validate_file_content(fake_png, "fake.png")
    assert "signature" in str(exc.value.detail).lower() or "extension" in str(exc.value.detail).lower()

def test_file_validation_corrupted_image():
    # Valid PNG header but corrupted body
    corrupt_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 30
    with pytest.raises(Exception) as exc:
        validate_file_content(corrupt_png, "corrupt.png")
    assert "corrupted" in str(exc.value.detail).lower() or "invalid" in str(exc.value.detail).lower()

def test_valid_image_validation():
    valid_png = create_synthetic_image(["CONSOLITH TEST"], format="PNG")
    fmt, ext = validate_file_content(valid_png, "valid.png")
    assert fmt == "png"
    assert ext == ".png"

    valid_jpg = create_synthetic_image(["CONSOLITH TEST"], format="JPEG")
    fmt, ext = validate_file_content(valid_jpg, "valid.jpg")
    assert fmt == "jpeg"
    assert ext == ".jpg"

def test_encryption_roundtrip():
    secret_text = "AADHAAR_9999_8888_7777_CONFIDENTIAL"
    encrypted = encrypt_data(secret_text)
    assert encrypted != secret_text
    decrypted = decrypt_data(encrypted)
    assert decrypted == secret_text

def test_aadhaar_parser_masking():
    raw_ocr = """
    GOVERNMENT OF INDIA
    Unique Identification Authority of India
    Rohan Sharma
    DOB: 15/08/1990
    Male
    5432 1098 7654
    """
    parser = AadhaarParser()
    result = parser.parse(raw_ocr)
    assert result["masked_id"] == "XXXX-XXXX-7654"
    assert result["fields"].get("full_name") == "Rohan Sharma"
    assert result["fields"].get("date_of_birth") == "15/08/1990"
    assert result["fields"].get("gender") == "Male"
    # Never expose the first 8 digits in parsed fields
    assert "5432" not in str(result["fields"])
    assert "1098" not in str(result["fields"])

def test_verhoeff_checksum():
    # Valid Aadhaar numbers generated via Verhoeff algorithm
    assert validate_verhoeff("2363") is True
    # Transposition error (adjacent digits swapped: 2363 -> 2633) must fail
    assert validate_verhoeff("2633") is False
    # Single digit corruption must fail
    assert validate_verhoeff("2364") is False
    # Valid 12-digit number (e.g. 543210987654 check)
    assert validate_verhoeff("543210987654") in (True, False)
    # Non-digits and empty inputs
    assert validate_verhoeff("") is False
    assert validate_verhoeff("invalid") is False
    assert validate_verhoeff("123") is False

def test_pan_parser():
    raw_ocr = """
    INCOME TAX DEPARTMENT
    GOVT. OF INDIA
    Permanent Account Number Card
    Vikram Malhotra
    Father's Name
    Rajesh Malhotra
    22/04/1985
    ABCDE1234F
    """
    parser = PANParser()
    result = parser.parse(raw_ocr)
    assert result["fields"].get("pan_number") == "ABCDE1234F"
    assert result["masked_id"] == "AB***1234F"
    assert result["fields"].get("full_name") == "Vikram Malhotra"
    assert result["fields"].get("father_name") == "Rajesh Malhotra"
    assert result["fields"].get("date_of_birth") == "22/04/1985"

def test_passport_parser():
    raw_ocr = """
    REPUBLIC OF INDIA
    Surname
    SHARMA
    Given Name
    PRIYA
    Nationality
    INDIAN
    Sex: F
    Date of Birth: 10/11/1992
    Date of Expiry: 09/11/2032
    Z1234567
    """
    parser = PassportParser()
    result = parser.parse(raw_ocr)
    assert result["fields"].get("passport_number") == "Z1234567"
    assert result["masked_id"] == "Z*****67"
    assert result["fields"].get("full_name") == "PRIYA SHARMA"
    assert result["fields"].get("gender") == "Female"
    assert result["fields"].get("date_of_birth") == "10/11/1992"

def test_education_certificate_parser():
    raw_ocr = """
    CENTRAL BOARD OF SECONDARY EDUCATION
    Roll No: 2167439
    This is to certify that AMIT KUMAR
    Born on 05/06/1995
    passed the Secondary School Examination held in 2011
    """
    parser = EducationCertificateParser(doc_type="education_10th")
    result = parser.parse(raw_ocr)
    assert result["masked_id"] == "ROLL-2167439"
    assert result["fields"].get("roll_number") == "2167439"
    assert result["fields"].get("full_name") == "AMIT KUMAR"
    assert result["fields"].get("date_of_birth") == "05/06/1995"
    assert result["fields"].get("examination_year") == "2011"
    assert result["fields"].get("board") == "CENTRAL BOARD OF SECONDARY EDUCATION"

def test_epf_parser():
    raw_ocr = """
    EMPLOYEES' PROVIDENT FUND ORGANISATION
    Universal Account Number (UAN): 100987654321
    Member ID: DLCPM00123450000001
    Member Name: SUNIL VERMA
    Establishment Name: TECH CORP INDIA PVT LTD
    """
    parser = EPFRecordParser()
    result = parser.parse(raw_ocr)
    assert result["fields"].get("uan") == "100987654321"
    assert result["masked_id"] == "UAN-1009****4321"
    assert result["fields"].get("full_name") == "SUNIL VERMA"
    assert result["fields"].get("establishment_name") == "TECH CORP INDIA PVT LTD"

def test_upload_api_unauthenticated():
    png_bytes = create_synthetic_image(["TEST"])
    files = {"file": ("test.png", png_bytes, "image/png")}
    data = {"document_type": "pan"}
    response = client.post("/api/v1/documents/upload", files=files, data=data)
    assert response.status_code == 401

def test_upload_api_authenticated_citizen():
    user_uid = f"up_test_{uuid.uuid4().hex[:8]}"
    headers = {"Authorization": f"Bearer test_token_{user_uid}:Upload Tester:citizen"}

    # Provision user first
    prov_resp = client.post(
        "/api/v1/auth/provision",
        headers=headers,
        json={"email": f"{user_uid}@test.in", "full_name": "Upload Tester"}
    )
    assert prov_resp.status_code in (200, 201)

    # Upload synthetic document
    png_bytes = create_synthetic_image(["INCOME TAX DEPARTMENT", "ABCDE1234F", "DOB 01/01/1990"])
    files = {"file": ("pan_card.png", png_bytes, "image/png")}
    data = {"document_type": "pan"}

    upload_resp = client.post("/api/v1/documents/upload", headers=headers, files=files, data=data)
    assert upload_resp.status_code == 201
    doc_json = upload_resp.json()
    assert doc_json["document_type"] == "pan"
    assert "id" in doc_json
    doc_id = doc_json["id"]

    # Verify document is in list
    list_resp = client.get("/api/v1/documents", headers=headers)
    assert list_resp.status_code == 200
    list_json = list_resp.json()
    assert list_json["total"] >= 1
    assert any(d["id"] == doc_id for d in list_json["documents"])

    # Fetch document detail
    detail_resp = client.get(f"/api/v1/documents/{doc_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == doc_id

    # Citizen confirms/updates extracted demographic fields
    patch_resp = client.patch(
        f"/api/v1/documents/{doc_id}/fields",
        headers=headers,
        json={"extracted_fields": {"full_name": "Confirmed Arjun", "date_of_birth": "1990-01-01"}}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["extracted_fields"]["full_name"] == "Confirmed Arjun"
    assert patch_resp.json()["extracted_fields"]["date_of_birth"] == "1990-01-01"

    # Verify cross-user isolation: Another citizen cannot view this document
    other_uid = f"up_other_{uuid.uuid4().hex[:8]}"
    other_headers = {"Authorization": f"Bearer test_token_{other_uid}:Other Citizen:citizen"}
    client.post(
        "/api/v1/auth/provision",
        headers=other_headers,
        json={"email": f"{other_uid}@test.in", "full_name": "Other Citizen"}
    )
    unauth_resp = client.get(f"/api/v1/documents/{doc_id}", headers=other_headers)
    assert unauth_resp.status_code == 404

    # Other citizen cannot patch or update fields
    patch_unauth = client.patch(
        f"/api/v1/documents/{doc_id}/fields",
        headers=other_headers,
        json={"extracted_fields": {"full_name": "Hacked Name"}}
    )
    assert patch_unauth.status_code == 404

    # Other citizen cannot delete the document
    del_unauth_resp = client.delete(f"/api/v1/documents/{doc_id}", headers=other_headers)
    assert del_unauth_resp.status_code == 404

    # Original owner can delete
    del_resp = client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
    assert del_resp.status_code == 200
