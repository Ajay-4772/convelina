import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal, set_rls_context
from app.models.document import Document
from app.models.conflict import Conflict
from app.conflicts.normalizer import normalize_name, parse_and_normalize_date, normalize_gender
from app.conflicts.matcher import match_names, match_dates_of_birth, match_gender
from app.conflicts.rules import evaluate_document_pair
from app.conflicts.engine import ConflictDetectionEngine, mask_sensitive_content

client = TestClient(app)

# -----------------------------------------------------------------------------
# UNIT TESTS: Normalizer
# -----------------------------------------------------------------------------

def test_normalize_name_title_and_whitespace():
    raw = "  Shri.  Rajesh   Kumar   "
    normalized, tokens = normalize_name(raw)
    assert normalized == "rajesh kumar"
    assert tokens == ["rajesh", "kumar"]

def test_normalize_name_punctuation_and_case():
    raw = "DR. A.K. SHARMA-VERMA"
    normalized, tokens = normalize_name(raw)
    assert "sharma" in tokens
    assert "verma" in tokens
    assert "dr" not in tokens

def test_normalize_name_empty():
    assert normalize_name("") == ("", [])
    assert normalize_name(None) == ("", [])

def test_normalize_date_valid_formats():
    d1, y1, m1, day1, s1 = parse_and_normalize_date("15/08/1947")
    assert s1 == "VALID"
    assert d1 == "1947-08-15"
    assert y1 == 1947 and m1 == 8 and day1 == 15

    d2, y2, m2, day2, s2 = parse_and_normalize_date("1995-12-31")
    assert s2 == "VALID"
    assert d2 == "1995-12-31"

def test_normalize_date_year_only():
    d, y, m, day, status = parse_and_normalize_date("1988")
    assert status == "YEAR_ONLY"
    assert d == "1988"
    assert y == 1988
    assert m is None and day is None

def test_normalize_date_invalid_and_missing():
    _, _, _, _, s_inv = parse_and_normalize_date("32/13/2020")
    assert s_inv == "INVALID"
    _, _, _, _, s_mis = parse_and_normalize_date("")
    assert s_mis == "MISSING"

def test_normalize_gender():
    assert normalize_gender("MALE") == "Male"
    assert normalize_gender("m") == "Male"
    assert normalize_gender("पुरुष") == "Male"
    assert normalize_gender("FEMALE") == "Female"
    assert normalize_gender("महिला") == "Female"
    assert normalize_gender("T") == "Transgender"
    assert normalize_gender(None) is None

# -----------------------------------------------------------------------------
# UNIT TESTS: Matcher
# -----------------------------------------------------------------------------

def test_match_names_exact():
    res = match_names("Rajesh Kumar", "Rajesh Kumar")
    assert res.category == "EXACT_MATCH"
    assert res.is_conflict is False

def test_match_names_normalized():
    # Shri is normalized away, resulting in identical normalized tokens
    res = match_names("Shri Rajesh Kumar", "rajesh kumar")
    assert res.category == "EXACT_MATCH"
    assert res.is_conflict is False

def test_match_names_token_permutation():
    res = match_names("Kumar Rajesh", "Rajesh Kumar")
    assert res.category == "TOKEN_REORDER"
    assert res.is_conflict is True
    assert res.conflict_type == "format-only"
    assert res.severity == "low"

def test_match_names_initials_expansion():
    res = match_names("R. Kumar", "Rajesh Kumar")
    assert res.category == "INITIALS_EXPANSION"
    assert res.is_conflict is True
    assert res.conflict_type == "unresolvable-needs-evidence"
    assert res.severity == "medium"

def test_match_names_ocr_character_substitutions():
    # Common OCR: 'O' vs '0', 'I' vs '1'
    res = match_names("AN1TA SHARMA", "ANITA SHARMA")
    assert res.category == "MINOR_TYPO"
    assert res.is_conflict is True
    assert res.conflict_type == "format-only"
    assert res.severity == "low"

def test_match_names_fuzzy_close():
    res = match_names("Vikramaditya Singh", "Vikramadtya Singh")
    assert res.category == "MINOR_TYPO"
    assert res.is_conflict is True
    assert res.conflict_type == "format-only"

def test_match_names_mismatch():
    res = match_names("Sunil Sharma", "Amit Patel")
    assert res.category == "CONFIRMED_MISMATCH"
    assert res.is_conflict is True
    assert res.conflict_type == "genuine-mismatch"
    assert res.severity == "critical"

def test_match_dates_exact():
    res = match_dates_of_birth("12/05/1990", "1990-05-12")
    assert res.category == "EXACT_MATCH"
    assert res.is_conflict is False

def test_match_dates_year_compatible():
    res = match_dates_of_birth("1990", "12/05/1990")
    assert res.category == "COMPATIBLE_YEAR"
    assert res.is_conflict is True
    assert res.conflict_type == "format-only"
    assert res.severity == "low"

def test_match_dates_mismatch():
    res = match_dates_of_birth("12/05/1990", "14/08/1992")
    assert res.category == "FULL_MISMATCH"
    assert res.is_conflict is True
    assert res.conflict_type == "genuine-mismatch"
    assert res.severity == "critical"

def test_match_dates_missing():
    res = match_dates_of_birth("", "14/08/1992")
    assert res.category == "MISSING_DATA"
    assert res.is_conflict is False

def test_match_gender_mismatch():
    res = match_gender("Male", "Female")
    assert res["is_conflict"] is True
    assert res["category"] == "GENDER_MISMATCH"
    assert res["severity"] == "high"

# -----------------------------------------------------------------------------
# UNIT TESTS: Rules & Pairwise Evaluation
# -----------------------------------------------------------------------------

def test_evaluate_document_pair_name_and_dob_discrepancy():
    doc_a = {
        "id": "1",
        "document_type": "aadhaar",
        "masked_id": "XXXX-XXXX-1234",
        "extracted_fields": {
            "full_name": "Ramesh Chandra Sharma",
            "date_of_birth": "05/10/1985",
            "gender": "Male",
        }
    }
    doc_b = {
        "id": "2",
        "document_type": "pan",
        "masked_id": "ABCDE1234F",
        "extracted_fields": {
            "full_name": "R. C. Sharma",
            "date_of_birth": "05/10/1985",
            "father_name": "Kailash Sharma",
        }
    }

    conflicts = evaluate_document_pair(doc_a, doc_b)
    # Should detect name discrepancy (initials) but DOB matches
    fields_detected = [c["field_name"] for c in conflicts]
    assert "full_name" in fields_detected
    assert "date_of_birth" not in fields_detected

def test_evaluate_document_pair_no_incompatible_cross_fields():
    # Passport vs Certificate
    doc_a = {
        "id": "1",
        "document_type": "passport",
        "masked_id": "P1234567",
        "extracted_fields": {
            "full_name": "Pooja Verma",
            "passport_expiry": "2030-01-01",
        }
    }
    doc_b = {
        "id": "2",
        "document_type": "education_10th",
        "masked_id": "ROLL-102938",
        "extracted_fields": {
            "full_name": "Pooja Verma",
            "passing_year": "2015",
        }
    }

    conflicts = evaluate_document_pair(doc_a, doc_b)
    # Expiry date should NOT be compared to passing year!
    assert len(conflicts) == 0

def test_mask_sensitive_content_helper():
    raw_aadhaar = "Discrepancy in Aadhaar 1234 5678 9012 vs record"
    masked = mask_sensitive_content(raw_aadhaar)
    assert "1234 5678" not in masked
    assert "XXXX-XXXX-9012" in masked

# -----------------------------------------------------------------------------
# API INTEGRATION TESTS: Conflicts Endpoints
# -----------------------------------------------------------------------------

def test_api_conflicts_unauthenticated():
    resp = client.post("/api/v1/conflicts/detect")
    assert resp.status_code == 401

    resp_list = client.get("/api/v1/conflicts")
    assert resp_list.status_code == 401

def test_api_conflicts_no_documents():
    user_uid = f"conf_nodoc_{uuid.uuid4().hex[:8]}"
    headers = {"Authorization": f"Bearer test_token_:{user_uid}:{user_uid}@test.in:No Doc Citizen"}

    client.post(
        "/api/v1/auth/provision",
        headers=headers,
        json={"email": f"{user_uid}@test.in", "full_name": "No Doc Citizen"}
    )

    resp = client.post("/api/v1/conflicts/detect", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_documents_analyzed"] == 0
    assert data["total_conflicts_detected"] == 0

def test_api_conflicts_full_workflow():
    user_uid = f"conf_flow_{uuid.uuid4().hex[:8]}"
    headers = {"Authorization": f"Bearer test_token_:{user_uid}:{user_uid}@test.in:Conflict Flow User"}

    prov_resp = client.post(
        "/api/v1/auth/provision",
        headers=headers,
        json={"email": f"{user_uid}@test.in", "full_name": "Conflict Flow User"}
    )
    user_id = uuid.UUID(prov_resp.json()["id"])

    # Directly seed 2 documents for this user in DB
    db = SessionLocal()
    try:
        set_rls_context(db, user_id, "citizen")

        doc1 = Document(
            user_id=user_id,
            document_type="aadhaar",
            file_path="ephemeral://synthetic_aadhaar",
            file_hash=uuid.uuid4().hex,
            ocr_status="completed",
            extracted_fields={
                "full_name": "Suresh Kumar",
                "date_of_birth": "1985-05-20",
                "gender": "Male",
            },
            masked_id="XXXX-XXXX-9999",
        )
        doc2 = Document(
            user_id=user_id,
            document_type="pan",
            file_path="ephemeral://synthetic_pan",
            file_hash=uuid.uuid4().hex,
            ocr_status="completed",
            extracted_fields={
                "full_name": "Suresh Chandra Kumar",  # Discrepancy (middle name)
                "date_of_birth": "1987-08-15",        # Discrepancy (different DOB)
            },
            masked_id="ABCDE5678G",
        )
        db.add(doc1)
        db.add(doc2)
        db.commit()
    finally:
        db.close()

    # 1. Trigger Conflict Detection
    detect_resp = client.post("/api/v1/conflicts/detect", headers=headers)
    assert detect_resp.status_code == 200
    det_json = detect_resp.json()
    assert det_json["total_documents_analyzed"] == 2
    assert det_json["total_conflicts_detected"] >= 2
    assert det_json["new_conflicts_created"] >= 2

    # Verify fields detected
    fields = [c["field_name"] for c in det_json["conflicts"]]
    assert "full_name" in fields
    assert "date_of_birth" in fields

    first_conflict = det_json["conflicts"][0]
    conflict_id = first_conflict["id"]

    # 2. List Conflicts
    list_resp = client.get("/api/v1/conflicts", headers=headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 2

    # 3. Get Conflict by ID
    get_resp = client.get(f"/api/v1/conflicts/{conflict_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == conflict_id

    # 4. Update Review Status
    review_resp = client.patch(
        f"/api/v1/conflicts/{conflict_id}/review",
        headers=headers,
        json={"status": "in_review"}
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["status"] == "in_review"

    # Bad status validation
    bad_review = client.patch(
        f"/api/v1/conflicts/{conflict_id}/review",
        headers=headers,
        json={"status": "invalid_status_xyz"}
    )
    assert bad_review.status_code == 400

    # 5. Idempotent re-run of detection: should not create duplicate records
    rerun_resp = client.post("/api/v1/conflicts/detect", headers=headers)
    assert rerun_resp.status_code == 200
    rerun_json = rerun_resp.json()
    assert rerun_json["new_conflicts_created"] == 0
    assert rerun_json["total_conflicts_detected"] == det_json["total_conflicts_detected"]

    # 6. Cross-User Isolation Enforcement
    other_uid = f"conf_other_{uuid.uuid4().hex[:8]}"
    other_headers = {"Authorization": f"Bearer test_token_:{other_uid}:{other_uid}@test.in:Other Citizen"}
    client.post(
        "/api/v1/auth/provision",
        headers=other_headers,
        json={"email": f"{other_uid}@test.in", "full_name": "Other Citizen"}
    )

    # Other citizen cannot view original user's conflict
    other_get = client.get(f"/api/v1/conflicts/{conflict_id}", headers=other_headers)
    assert other_get.status_code == 404

    # Other citizen cannot update original user's conflict review status
    other_patch = client.patch(
        f"/api/v1/conflicts/{conflict_id}/review",
        headers=other_headers,
        json={"status": "resolved"}
    )
    assert other_patch.status_code == 404
