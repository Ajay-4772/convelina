"""
CONVELINA - End-to-End Real Functional Audit Script
Tests the real live user journey end-to-end against the running backend with synthetic test fixtures.
"""

import io
import json
import os
import sys
import uuid
from typing import Dict, Any

from PIL import Image, ImageDraw
import psycopg2
from fastapi.testclient import TestClient

# Ensure backend app is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

try:
    from app.main import app  # type: ignore[import-not-found, import-untyped]
    from app.core.database import SessionLocal, set_rls_context  # type: ignore[import-not-found, import-untyped]
except ImportError:
    from backend.app.main import app  # type: ignore[import-not-found, import-untyped]
    from backend.app.core.database import SessionLocal, set_rls_context  # type: ignore[import-not-found, import-untyped]

client = TestClient(app)

ADMIN_DB_URL = os.getenv(
    "DATABASE_MIGRATION_URL",
    "postgresql://postgres:postgres_dev_password@postgres:5432/consolith"
)

def create_synthetic_card_image(lines: list, width=500, height=280) -> bytes:
    """Generates a clean synthetic document image in memory."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    y = 25
    for line in lines:
        draw.text((25, y), line, fill=(0, 0, 0))
        y += 32
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def run_functional_audit():
    print("=" * 65)
    print("  CONVELINA REAL END-TO-END FUNCTIONAL AUDIT")
    print("=" * 65)

    results = {}

    # 1. Health Checks
    print("\n[STEP 1] Probing Health Endpoints...")
    res_health = client.get("/health")
    assert res_health.status_code == 200, f"Health failed: {res_health.status_code}"
    res_auth_health = client.get("/api/v1/auth/health")
    assert res_auth_health.status_code == 200, f"Auth health failed: {res_auth_health.status_code}"
    print(f"  [PASS] /health -> 200 ({res_health.json()})")
    print(f"  [PASS] /api/v1/auth/health -> 200 ({res_auth_health.json()})")
    results["health_probes"] = "PASS"

    # 2. User Provisioning & Authentication
    print("\n[STEP 2] Simulating User 1 Signup & Provisioning...")
    uid_1 = f"e2e_user1_{uuid.uuid4().hex[:8]}"
    email_1 = f"{uid_1}@synthetic.test"
    token_1 = f"test_token_:{uid_1}:{email_1}:Ajay Ramanathan"

    res_prov = client.post(
        "/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {token_1}"},
        json={"full_name": "Ajay Ramanathan", "role": "user"}
    )
    assert res_prov.status_code in [200, 201], f"Provision failed: {res_prov.status_code}"
    user_1_data = res_prov.json()
    user_1_id = user_1_data["id"]
    assert user_1_data["role"] in ["user", "citizen"]
    print(f"  [PASS] User 1 provisioned (ID: {user_1_id}, Role: {user_1_data['role']})")
    results["auth_provision"] = "PASS"

    # 3. Profile Setup & Management
    print("\n[STEP 3] Updating and Resolving User 1 Profile...")
    res_profile_update = client.patch(
        "/api/v1/auth/profile",
        headers={"Authorization": f"Bearer {token_1}"},
        json={
            "full_name": "M Ajay Ramanathan",
            "date_of_birth": "1995-05-15",
            "phone_number": "+919876543210",
            "address": "42 Anna Salai, Chennai, Tamil Nadu 600002",
            "father_name": "Muthu Ramanathan"
        }
    )
    assert res_profile_update.status_code == 200, f"Profile update failed: {res_profile_update.status_code}"
    prof = res_profile_update.json()
    assert prof["full_name"] == "M Ajay Ramanathan"
    assert prof["date_of_birth"] == "1995-05-15"

    res_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_1}"})
    assert res_me.status_code == 200
    assert res_me.json()["email"] == email_1
    print(f"  [PASS] Profile stored and retrieved accurately (Name: {prof['full_name']})")
    results["profile_system"] = "PASS"

    # 4. Document Upload & Temporary Processing (Document 1: Synthetic Aadhaar)
    print("\n[STEP 4] Document 1 Upload: Synthetic Aadhaar Card...")
    aadhaar_bytes = create_synthetic_card_image([
        "GOVERNMENT OF INDIA",
        "Unique Identification Authority of India",
        "M Ajay",
        "DOB: 15/05/1995",
        "Male",
        "5432 1098 7654"
    ])
    files_aadhaar = {"file": ("aadhaar_sample.png", aadhaar_bytes, "image/png")}
    data_aadhaar = {"document_type": "aadhaar"}

    res_up1 = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token_1}"},
        data=data_aadhaar,
        files=files_aadhaar
    )
    assert res_up1.status_code == 201, f"Aadhaar upload failed: {res_up1.status_code} - {res_up1.text}"
    doc1_data = res_up1.json()
    doc1_id = doc1_data["id"]
    print(f"  [PASS] Aadhaar uploaded: ID={doc1_id}, status={doc1_data['ocr_status']}")
    print(f"         Masked ID: {doc1_data.get('masked_id')}")
    print(f"         Extracted Fields: {doc1_data.get('extracted_fields')}")
    # Verify Aadhaar Act privacy: first 8 digits must never be present
    assert "5432" not in str(doc1_data)
    assert "1098" not in str(doc1_data)
    assert doc1_data.get("masked_id") == "XXXX-XXXX-7654"
    results["upload_doc1_aadhaar"] = "PASS"

    # 5. Document Upload & Temporary Processing (Document 2: Synthetic PAN)
    print("\n[STEP 5] Document 2 Upload: Synthetic PAN Card...")
    pan_bytes = create_synthetic_card_image([
        "INCOME TAX DEPARTMENT",
        "GOVT OF INDIA",
        "AJAY MUTHU",
        "Father's Name",
        "MUTHUKUMAR M",
        "15/05/1995",
        "ABCDE1234F"
    ])
    files_pan = {"file": ("pan_sample.png", pan_bytes, "image/png")}
    data_pan = {"document_type": "pan"}

    res_up2 = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {token_1}"},
        data=data_pan,
        files=files_pan
    )
    assert res_up2.status_code == 201, f"PAN upload failed: {res_up2.status_code} - {res_up2.text}"
    doc2_data = res_up2.json()
    doc2_id = doc2_data["id"]
    print(f"  [PASS] PAN uploaded: ID={doc2_id}, status={doc2_data['ocr_status']}")
    print(f"         Masked ID: {doc2_data.get('masked_id')}")
    print(f"         Extracted Fields: {doc2_data.get('extracted_fields')}")
    results["upload_doc2_pan"] = "PASS"

    # 6. Document Listing Under RLS
    print("\n[STEP 6] Listing User 1's Uploaded Documents...")
    res_docs = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {token_1}"})
    assert res_docs.status_code == 200
    docs_list = res_docs.json()["documents"]
    assert len(docs_list) >= 2
    print(f"  [PASS] User 1 has {len(docs_list)} documents stored under RLS.")
    results["document_listing"] = "PASS"

    # 7. Conflict Detection Engine
    print("\n[STEP 7] Running Cross-Document Conflict Detection...")
    res_detect = client.post("/api/v1/conflicts/detect", headers={"Authorization": f"Bearer {token_1}"})
    assert res_detect.status_code == 200, f"Detection failed: {res_detect.status_code} - {res_detect.text}"
    detect_data = res_detect.json()
    print(f"  [PASS] Analyzed: {detect_data['total_documents_analyzed']} docs, Found: {detect_data['total_conflicts_detected']} conflicts.")
    for c in detect_data.get("conflicts", []):
        print(f"         - Field: {c['field_name']} | Type: {c['conflict_type']} | Severity: {c['severity']}")
        print(f"           Doc A: '{c['value_a']}' vs Doc B: '{c['value_b']}'")
        print(f"           Note: {c['description']}")
    results["conflict_detection"] = "PASS"

    # 8. Forms Catalog Query
    print("\n[STEP 8] Querying Official Statutory Forms Catalog...")
    res_forms = client.get("/api/v1/knowledge/forms", headers={"Authorization": f"Bearer {token_1}"})
    assert res_forms.status_code == 200
    forms = res_forms.json().get("forms", [])
    assert len(forms) >= 6
    print(f"  [PASS] Retrieved {len(forms)} verified official forms from catalog.")
    sample_form = forms[0]
    print(f"         Form: {sample_form['form_name']} ({sample_form['form_id']})")
    print(f"         Download URL: {sample_form.get('official_download_url')}")
    results["forms_catalog"] = "PASS"

    # 9. AI Assistant RAG Query
    print("\n[STEP 9] Querying AI Resolution Assistant...")
    res_chat = client.post(
        "/api/v1/assistant/chat",
        headers={"Authorization": f"Bearer {token_1}"},
        json={
            "message": "How do I correct my father's name discrepancy in PAN card to match my Aadhaar?",
            "document_category": "pan"
        }
    )
    assert res_chat.status_code == 200, f"Chat failed: {res_chat.status_code} - {res_chat.text}"
    chat_data = res_chat.json()
    conv_id = chat_data["conversation_id"]
    ans = chat_data["response"]
    print(f"  [PASS] Conversation created: ID={conv_id}")
    print(f"         Assistant Answer: {ans.get('answer')[:120]}...")
    print(f"         Confidence: {ans.get('confidence')}")
    print(f"         Resolution Steps: {len(ans.get('resolution_steps', []))} steps provided.")
    print(f"         Citations: {len(ans.get('citations', []))} official citations.")
    results["assistant_chat"] = "PASS"

    # 10. AI Assistant Conversation Management & Deletion
    print("\n[STEP 10] Deleting Assistant Conversation...")
    res_del_conv = client.delete(
        f"/api/v1/assistant/conversations/{conv_id}",
        headers={"Authorization": f"Bearer {token_1}"}
    )
    assert res_del_conv.status_code == 204
    # Verify conversation is gone
    res_list_convs = client.get("/api/v1/assistant/conversations", headers={"Authorization": f"Bearer {token_1}"})
    conv_ids = [c["id"] for c in res_list_convs.json().get("conversations", [])]
    assert conv_id not in conv_ids
    print("  [PASS] Conversation deleted successfully and confirmed absent.")
    results["assistant_deletion"] = "PASS"

    # 11. Cross-Tenant RLS & IDOR Security Verification
    print("\n[STEP 11] Cross-Tenant RLS Isolation Verification with User 2...")
    uid_2 = f"e2e_user2_{uuid.uuid4().hex[:8]}"
    email_2 = f"{uid_2}@synthetic.test"
    token_2 = f"test_token_:{uid_2}:{email_2}:Vijay Kumar"

    client.post(
        "/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {token_2}"},
        json={"full_name": "Vijay Kumar", "role": "user"}
    )

    # User 2 lists documents -> must see 0 of User 1's documents
    res_u2_docs = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {token_2}"})
    u2_docs = res_u2_docs.json()["documents"]
    assert len(u2_docs) == 0, f"Cross-tenant leak! User 2 saw {len(u2_docs)} documents."
    print("  [PASS] User 2 sees 0 of User 1's documents.")

    # User 2 attempts to fetch User 1's specific document ID -> HTTP 404
    res_u2_doc1 = client.get(f"/api/v1/documents/{doc1_id}", headers={"Authorization": f"Bearer {token_2}"})
    assert res_u2_doc1.status_code == 404, f"Expected 404, got {res_u2_doc1.status_code}"
    print("  [PASS] User 2 direct IDOR probe against User 1 document rejected (HTTP 404).")

    # User 2 attempts to access Admin endpoints -> HTTP 403 Forbidden
    res_u2_admin = client.get("/api/v1/admin/overview-stats", headers={"Authorization": f"Bearer {token_2}"})
    assert res_u2_admin.status_code == 403, f"Expected 403, got {res_u2_admin.status_code}"
    print("  [PASS] User 2 unauthorized admin route probe rejected (HTTP 403).")
    results["rls_and_security_isolation"] = "PASS"

    # 12. Admin Management Endpoints
    print("\n[STEP 12] Testing Admin Management APIs...")
    adm_uid = f"e2e_adm_{uuid.uuid4().hex[:8]}"
    adm_email = f"{adm_uid}@synthetic.test"
    adm_token = f"test_token_:{adm_uid}:{adm_email}:Super Administrator"

    client.post(
        "/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {adm_token}"},
        json={"full_name": "Super Administrator"}
    )

    # Grant admin in DB
    conn = psycopg2.connect(ADMIN_DB_URL)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SET LOCAL app.current_user_role = 'admin';")
        cur.execute("UPDATE users SET role = 'admin' WHERE firebase_uid = %s;", (adm_uid,))
    conn.close()

    res_adm_stats = client.get("/api/v1/admin/overview-stats", headers={"Authorization": f"Bearer {adm_token}"})
    assert res_adm_stats.status_code == 200
    stats = res_adm_stats.json()
    print(f"  [PASS] Admin Overview Stats: {stats['users']['total']} users, {stats['documents']['total_uploaded']} docs, {stats['conflicts']['total_detected']} conflicts.")

    res_adm_users = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {adm_token}"})
    assert res_adm_users.status_code == 200
    print(f"  [PASS] Admin Users Query: retrieved {len(res_adm_users.json())} users.")

    res_adm_docs = client.get("/api/v1/admin/documents", headers={"Authorization": f"Bearer {adm_token}"})
    assert res_adm_docs.status_code == 200
    print(f"  [PASS] Admin Documents Monitoring: retrieved {len(res_adm_docs.json())} documents across platform.")

    results["admin_portal_apis"] = "PASS"

    print("\n" + "=" * 65)
    print("  ALL 12 END-TO-END FUNCTIONAL AUDIT TESTS PASSED!")
    print("=" * 65)
    return results

if __name__ == "__main__":
    run_functional_audit()
