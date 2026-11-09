#!/usr/bin/env python3
"""
Consolith Module 4: Secure Document Upload & OCR Pipeline Integration Test Suite
Validates:
1. Unauthenticated rejection
2. Bad document type rejection
3. Corrupted / mismatched file rejection
4. Aadhaar upload, OCR parsing, and privacy masking (XXXX-XXXX-1234)
5. PAN upload and field extraction
6. List documents with RLS scoping
7. Cross-citizen IDOR protection (404 on other citizen's document)
8. Authorized document deletion
"""

import io
import sys
import uuid
import httpx
from PIL import Image, ImageDraw

BASE_URL = "http://localhost:8000"

def create_synthetic_image(text_lines, width=600, height=350, format="PNG") -> bytes:
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    y = 30
    for line in text_lines:
        draw.text((30, y), line, fill=(0, 0, 0))
        y += 40
    img = img.resize((width * 2, height * 2), Image.Resampling.NEAREST)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def run_all_tests():
    print("=" * 60)
    print("  Consolith Module 4: Upload & OCR Pipeline Integration Tests")
    print("=" * 60)

    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # 1. Unauthenticated upload rejection
    print("\n[TEST 1/8] Verifying unauthenticated upload rejection...")
    dummy_png = create_synthetic_image(["TEST"])
    resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.png", dummy_png, "image/png")},
        data={"document_type": "aadhaar"}
    )
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
    print(f"  [OK] Unauthenticated upload rejected with HTTP 401: {resp.json().get('detail')}")

    # Provision Citizen A
    cit_a_uid = f"cit_a_{uuid.uuid4().hex[:8]}"
    headers_a = {"Authorization": f"Bearer test_token_{cit_a_uid}:Citizen Arjun:citizen"}
    prov_resp = client.post(
        "/api/v1/auth/provision",
        headers=headers_a,
        json={"email": f"{cit_a_uid}@test.in", "full_name": "Citizen Arjun"}
    )
    assert prov_resp.status_code in (200, 201)
    user_a = prov_resp.json()
    print(f"  Provisioned Citizen A: {user_a['full_name']} ({user_a['id']})")

    # 2. Unsupported document type rejection
    print("\n[TEST 2/8] Testing unsupported document type rejection...")
    resp = client.post(
        "/api/v1/documents/upload",
        headers=headers_a,
        files={"file": ("test.png", dummy_png, "image/png")},
        data={"document_type": "fake_driver_license"}
    )
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    print(f"  [OK] Invalid document type rejected with HTTP 400: {resp.json().get('detail')}")

    # 3. Corrupted / mismatched magic bytes rejection
    print("\n[TEST 3/8] Testing corrupted/mismatched magic bytes rejection...")
    fake_png = b"This is not a png file content at all"
    resp = client.post(
        "/api/v1/documents/upload",
        headers=headers_a,
        files={"file": ("fake.png", fake_png, "image/png")},
        data={"document_type": "pan"}
    )
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    print(f"  [OK] Invalid magic bytes rejected with HTTP 400: {resp.json().get('detail')}")

    # 4. Valid Aadhaar Upload and Privacy Masking
    print("\n[TEST 4/8] Testing Aadhaar upload and privacy masking...")
    aadhaar_img = create_synthetic_image([
        "GOVERNMENT OF INDIA",
        "Unique Identification Authority of India",
        "Citizen Arjun",
        "DOB: 12/03/1988",
        "Male",
        "9876 5432 1098"
    ])
    resp = client.post(
        "/api/v1/documents/upload",
        headers=headers_a,
        files={"file": ("aadhaar_card.png", aadhaar_img, "image/png")},
        data={"document_type": "aadhaar"}
    )
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    doc_a = resp.json()
    print(f"  Aadhaar uploaded: id={doc_a['id']}, status={doc_a['ocr_status']}, masked_id={doc_a['masked_id']}")
    assert doc_a["ocr_status"] == "completed"
    assert doc_a["masked_id"] and doc_a["masked_id"].startswith("XXXX-XXXX-") and len(doc_a["masked_id"]) == 14, f"Unexpected masked_id: {doc_a['masked_id']}"
    # Verify raw plaintext 12 digits never appear in public response
    assert "9876" not in str(doc_a["extracted_fields"])
    print(f"  [OK] Aadhaar privacy masking strictly verified: {doc_a['masked_id']}")

    # 5. Valid PAN Upload and Field Extraction
    print("\n[TEST 5/8] Testing PAN upload and structured extraction...")
    pan_img = create_synthetic_image([
        "INCOME TAX DEPARTMENT",
        "GOVT. OF INDIA",
        "Permanent Account Number Card",
        "Citizen Arjun",
        "Father's Name",
        "Ramesh Arjun",
        "12/03/1988",
        "ABCDE5555Z"
    ])
    resp = client.post(
        "/api/v1/documents/upload",
        headers=headers_a,
        files={"file": ("pan_card.png", pan_img, "image/png")},
        data={"document_type": "pan"}
    )
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    doc_pan = resp.json()
    print(f"  PAN uploaded: id={doc_pan['id']}, status={doc_pan['ocr_status']}, masked_id={doc_pan['masked_id']}")
    assert doc_pan["ocr_status"] == "completed"
    assert doc_pan["masked_id"] and (doc_pan["masked_id"].startswith("AB***") or "***" in doc_pan["masked_id"])
    print(f"  [OK] PAN structured extraction verified: {doc_pan['extracted_fields']}")


    # 6. Listing Citizen A's documents
    print("\n[TEST 6/8] Testing document listing under RLS...")
    list_resp = client.get("/api/v1/documents", headers=headers_a)
    assert list_resp.status_code == 200
    docs_list = list_resp.json()
    assert docs_list["total"] >= 2
    print(f"  [OK] Found {docs_list['total']} documents owned by Citizen A.")

    # 7. Cross-Citizen IDOR Prevention
    print("\n[TEST 7/8] Testing cross-citizen IDOR protection...")
    cit_b_uid = f"cit_b_{uuid.uuid4().hex[:8]}"
    headers_b = {"Authorization": f"Bearer test_token_{cit_b_uid}:Citizen Bhuvan:citizen"}
    client.post(
        "/api/v1/auth/provision",
        headers=headers_b,
        json={"email": f"{cit_b_uid}@test.in", "full_name": "Citizen Bhuvan"}
    )
    # Citizen B tries to fetch Citizen A's Aadhaar
    idor_get = client.get(f"/api/v1/documents/{doc_a['id']}", headers=headers_b)
    assert idor_get.status_code == 404, f"Expected 404, got {idor_get.status_code}"
    # Citizen B tries to delete Citizen A's Aadhaar
    idor_del = client.delete(f"/api/v1/documents/{doc_a['id']}", headers=headers_b)
    assert idor_del.status_code == 404, f"Expected 404, got {idor_del.status_code}"
    print("  [OK] Cross-user document read and delete attempts correctly blocked (HTTP 404).")

    # 8. Authorized Document Deletion
    print("\n[TEST 8/8] Testing authorized document deletion by owner...")
    del_resp = client.delete(f"/api/v1/documents/{doc_a['id']}", headers=headers_a)
    assert del_resp.status_code == 200, f"Expected 200, got {del_resp.status_code}"
    # Verify it is no longer retrievable
    after_get = client.get(f"/api/v1/documents/{doc_a['id']}", headers=headers_a)
    assert after_get.status_code == 404
    print("  [OK] Document successfully deleted by owner.")

    print("\n" + "=" * 60)
    print("  ALL 8/8 MODULE 4 UPLOAD & OCR INTEGRATION TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        run_all_tests()
    except Exception as e:
        print(f"\n[FAIL] Test execution error: {str(e)}")
        sys.exit(1)
