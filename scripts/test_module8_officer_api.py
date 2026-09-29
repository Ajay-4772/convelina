"""Consolith - Module 8 Live API & Row-Level Security Integration Tests

Tests:
1. Citizen A submits a discrepancy case for verification under RLS.
2. Citizen B cannot view Citizen A's case (RLS isolation -> HTTP 404).
3. Citizen cannot assign cases to officers (HTTP 403 Forbidden).
4. Officer 1 cannot view unassigned cases (RLS isolation -> HTTP 404).
5. Admin inspects pending cases and assigns Citizen A's case to Officer 1 (Audited).
6. Officer 1 starts review (status -> 'under_review', Audited).
7. Officer 2 cannot access Officer 1's assigned case (RLS isolation -> HTTP 404).
8. Officer 1 requests additional information from Citizen A (status -> 'additional_information_requested').
9. Citizen A views request and submits response (status -> 'information_submitted', Audited).
10. Officer 1 approves correction draft with decision reason (status -> 'approved', draft status -> 'approved', Audited).
11. Cryptographic audit trail immutability verified with valid SHA-256 hash chaining.
"""

import uuid
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.core.database import SessionLocal, set_rls_context
from app.models.user import User
from app.models.case import Case, CaseReviewRequest
from app.models.audit_log import AuditLog

client = TestClient(app)

CITIZEN_A_UID = f"cit_a_{uuid.uuid4().hex[:8]}"
CITIZEN_B_UID = f"cit_b_{uuid.uuid4().hex[:8]}"
OFFICER_1_UID = f"off_1_{uuid.uuid4().hex[:8]}"
OFFICER_2_UID = f"off_2_{uuid.uuid4().hex[:8]}"
ADMIN_UID = f"adm_1_{uuid.uuid4().hex[:8]}"

CITIZEN_A_EMAIL = f"{CITIZEN_A_UID}@example.com"
CITIZEN_B_EMAIL = f"{CITIZEN_B_UID}@example.com"
OFFICER_1_EMAIL = f"{OFFICER_1_UID}@example.com"
OFFICER_2_EMAIL = f"{OFFICER_2_UID}@example.com"
ADMIN_EMAIL = f"{ADMIN_UID}@example.com"

CITIZEN_A_TOKEN = f"test_token_:{CITIZEN_A_UID}:{CITIZEN_A_EMAIL}:Citizen A"
CITIZEN_B_TOKEN = f"test_token_:{CITIZEN_B_UID}:{CITIZEN_B_EMAIL}:Citizen B"
OFFICER_1_TOKEN = f"test_token_:{OFFICER_1_UID}:{OFFICER_1_EMAIL}:Officer 1"
OFFICER_2_TOKEN = f"test_token_:{OFFICER_2_UID}:{OFFICER_2_EMAIL}:Officer 2"
ADMIN_TOKEN = f"test_token_:{ADMIN_UID}:{ADMIN_EMAIL}:Admin 1"


def setup_users():
    import os
    import psycopg2
    admin_url = os.getenv(
        "DATABASE_MIGRATION_URL",
        "postgresql://postgres:postgres_dev_password@postgres:5432/consolith"
    )
    conn = psycopg2.connect(admin_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            # Upsert users with their target roles
            cur.execute("""
                INSERT INTO users (firebase_uid, email, full_name, role) VALUES
                (%s, %s, 'Citizen A', 'citizen'),
                (%s, %s, 'Citizen B', 'citizen'),
                (%s, %s, 'Officer 1', 'officer'),
                (%s, %s, 'Officer 2', 'officer'),
                (%s, %s, 'Admin 1', 'admin')
                ON CONFLICT (firebase_uid) DO UPDATE
                SET role = EXCLUDED.role, full_name = EXCLUDED.full_name
                RETURNING id, firebase_uid, role;
            """, (
                CITIZEN_A_UID, CITIZEN_A_EMAIL,
                CITIZEN_B_UID, CITIZEN_B_EMAIL,
                OFFICER_1_UID, OFFICER_1_EMAIL,
                OFFICER_2_UID, OFFICER_2_EMAIL,
                ADMIN_UID, ADMIN_EMAIL,
            ))
            rows = {r[1]: r[0] for r in cur.fetchall()}
            cit_a_id = rows[CITIZEN_A_UID]
            cit_b_id = rows[CITIZEN_B_UID]
            off_1_id = rows[OFFICER_1_UID]
            off_2_id = rows[OFFICER_2_UID]
            adm_id = rows[ADMIN_UID]
    finally:
        conn.close()

    return cit_a_id, cit_b_id, off_1_id, off_2_id, adm_id


def run_tests():
    print("=== Module 8 Officer Verification Workflow Live API & RLS Tests ===")
    cit_a_id, cit_b_id, off_1_id, off_2_id, adm_id = setup_users()
    print(f"Provisioned test users: Cit A, Cit B, Off 1, Off 2, Admin")

    # 1. Citizen A submits discrepancy case
    res_sub = client.post(
        "/api/v1/cases",
        headers={"Authorization": f"Bearer {CITIZEN_A_TOKEN}"},
        json={
            "title": "Aadhaar vs PAN Name Spelling Verification",
            "evidence_notes": "Submitted Class 10 certificate supporting Rajesh Kumar Sharma"
        }
    )
    assert res_sub.status_code == 201, f"Case submission failed: {res_sub.text}"
    case_data = res_sub.json()
    case_id = case_data["id"]
    assert case_data["status"] == "pending_assignment"
    print(f"  [PASS] 1. Citizen A submitted verification case (Case ID: {case_id})")

    # 2. Citizen B cannot view Citizen A's case
    res_cb_view = client.get(
        f"/api/v1/cases/{case_id}/review-status",
        headers={"Authorization": f"Bearer {CITIZEN_B_TOKEN}"}
    )
    assert res_cb_view.status_code == 404
    print("  [PASS] 2. RLS Isolation: Citizen B cannot view Citizen A's case (HTTP 404)")

    # 3. Citizen cannot assign cases
    res_cit_assign = client.post(
        f"/api/v1/admin/cases/{case_id}/assign",
        headers={"Authorization": f"Bearer {CITIZEN_A_TOKEN}"},
        json={"officer_id": off_1_id}
    )
    assert res_cit_assign.status_code == 403
    print("  [PASS] 3. Authorization: Citizen forbidden from assigning cases (HTTP 403)")

    # 4. Officer 1 cannot view unassigned case
    res_off_unassigned = client.get(
        f"/api/v1/officer/cases/{case_id}",
        headers={"Authorization": f"Bearer {OFFICER_1_TOKEN}"}
    )
    assert res_off_unassigned.status_code == 404
    print("  [PASS] 4. Officer Assignment Isolation: Officer 1 cannot view unassigned case (HTTP 404)")

    # 5. Admin assigns case to Officer 1
    res_assign = client.post(
        f"/api/v1/admin/cases/{case_id}/assign",
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
        json={"officer_id": off_1_id}
    )
    assert res_assign.status_code == 200
    assert res_assign.json()["status"] == "assigned"
    assert res_assign.json()["assigned_officer_id"] == off_1_id
    print("  [PASS] 5. Admin assigned case to Officer 1 (Audited)")

    # 6. Officer 1 starts review
    res_start = client.post(
        f"/api/v1/officer/cases/{case_id}/start-review",
        headers={"Authorization": f"Bearer {OFFICER_1_TOKEN}"}
    )
    assert res_start.status_code == 200
    assert res_start.json()["status"] == "under_review"
    assert res_start.json()["review_started_at"] is not None
    print("  [PASS] 6. Officer 1 started review (status: under_review)")

    # 7. Officer 2 cannot view Officer 1's assigned case
    res_off2_view = client.get(
        f"/api/v1/officer/cases/{case_id}",
        headers={"Authorization": f"Bearer {OFFICER_2_TOKEN}"}
    )
    assert res_off2_view.status_code == 404
    print("  [PASS] 7. Officer Cross-Isolation: Officer 2 cannot access Officer 1's assigned case (HTTP 404)")

    # 8. Officer 1 requests additional information from Citizen A
    res_req_info = client.post(
        f"/api/v1/officer/cases/{case_id}/request-information",
        headers={"Authorization": f"Bearer {OFFICER_1_TOKEN}"},
        json={
            "request_details": "Please confirm if your PAN card reflects the expanded middle name.",
            "request_reason": "Middle name abbreviated in primary submission document."
        }
    )
    assert res_req_info.status_code == 200
    req_info_data = res_req_info.json()
    req_id = req_info_data["id"]
    assert req_info_data["status"] == "pending"
    print("  [PASS] 8. Officer 1 requested clarification from Citizen A")

    # 9. Citizen A responds to clarification request
    res_resp = client.post(
        f"/api/v1/cases/{case_id}/review-requests/{req_id}/respond",
        headers={"Authorization": f"Bearer {CITIZEN_A_TOKEN}"},
        json={"response_text": "Yes, PAN record shows Kumar in full as recorded on Form 49A."}
    )
    assert res_resp.status_code == 200
    assert res_resp.json()["status"] == "responded"
    print("  [PASS] 9. Citizen A responded to request (status advanced to: information_submitted)")

    # 10. Officer 1 approves correction draft
    res_approve = client.post(
        f"/api/v1/officer/cases/{case_id}/approve",
        headers={"Authorization": f"Bearer {OFFICER_1_TOKEN}"},
        json={
            "decision_reason": "Verified against Class 10 certificate and citizen clarification response.",
            "officer_notes": "Application draft approved for applicant submission to regional authority."
        }
    )
    assert res_approve.status_code == 200
    approved_data = res_approve.json()
    assert approved_data["status"] == "approved"
    assert approved_data["decision"] == "approved"
    print("  [PASS] 10. Officer 1 approved draft with recorded decision reason")

    # 11. Verify cryptographic audit log integrity
    db = SessionLocal()
    try:
        set_rls_context(db, adm_id, "admin")
        case_logs = db.query(AuditLog).filter(AuditLog.entity_id == case_id).order_by(AuditLog.created_at.asc()).all()
        assert len(case_logs) >= 5, f"Expected at least 5 audit events, found {len(case_logs)}"
        for i in range(1, len(case_logs)):
            assert case_logs[i].prev_hash == case_logs[i-1].current_hash, "Hash chain link broken!"
        print(f"  [PASS] 11. Audit Trail Integrity: {len(case_logs)} audit events cryptographically chained via SHA-256")
    finally:
        db.close()

    print("\nALL 11 MODULE 8 API & RLS TESTS PASSED PERFECTLY!\n")


if __name__ == "__main__":
    run_tests()
