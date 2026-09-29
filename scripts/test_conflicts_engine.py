#!/usr/bin/env python3
"""
Consolith Module 5: Conflict Detection Engine Integration Test Script
Runs against the running backend to verify:
- End-to-end conflict detection across synthetic identity documents
- Deduplication and idempotency
- RLS isolation on conflicts
- Review status updates
- Defense-in-depth Aadhaar masking
"""

import sys
import uuid
import requests

BACKEND_URL = "http://localhost:8000"

def run_tests():
    print("==================================================")
    print("   Consolith Module 5: Conflict Detection Tests   ")
    print("==================================================")

    # 1. Unauthenticated detection rejection
    print("\n[TEST 1] Testing unauthenticated conflict detection rejection...")
    resp = requests.post(f"{BACKEND_URL}/api/v1/conflicts/detect")
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
    print("  [PASS] Unauthenticated request correctly rejected with 401.")

    # 2. Provision Citizen A
    uid_a = f"cit_a_{uuid.uuid4().hex[:8]}"
    token_a = f"Bearer test_token_:{uid_a}:{uid_a}@test.in:Citizen Alpha"
    headers_a = {"Authorization": token_a}

    print(f"\n[TEST 2] Provisioning Citizen A ({uid_a})...")
    prov_a = requests.post(
        f"{BACKEND_URL}/api/v1/auth/provision",
        headers=headers_a,
        json={"email": f"{uid_a}@test.in", "full_name": "Citizen Alpha"}
    )
    assert prov_a.status_code in (200, 201), f"Provision failed: {prov_a.text}"
    user_a_id = prov_a.json()["id"]
    print(f"  [PASS] Citizen A provisioned with ID: {user_a_id}")

    # 3. Detect conflicts with 0 documents
    print("\n[TEST 3] Running conflict detection with 0 documents...")
    det_empty = requests.post(f"{BACKEND_URL}/api/v1/conflicts/detect", headers=headers_a)
    assert det_empty.status_code == 200
    json_empty = det_empty.json()
    assert json_empty["total_documents_analyzed"] == 0
    assert json_empty["total_conflicts_detected"] == 0
    print("  [PASS] Zero document condition handled gracefully.")

    # 4. Upload 2 synthetic documents for Citizen A via documents API
    print("\n[TEST 4] Uploading synthetic Aadhaar and PAN documents...")
    import io
    from PIL import Image, ImageDraw

    def make_image(text_lines):
        img = Image.new("RGB", (600, 300), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        y = 30
        for line in text_lines:
            draw.text((30, y), line, fill=(0, 0, 0))
            y += 40
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    aadhaar_img = make_image([
        "GOVERNMENT OF INDIA",
        "Name: ANAND SHARMA",
        "DOB: 12/05/1988",
        "Gender: Male",
        "Aadhaar: 9876 5432 1098"
    ])
    pan_img = make_image([
        "INCOME TAX DEPARTMENT",
        "Permanent Account Number",
        "ABCDE1234F",
        "Name: A. SHARMA",
        "Father: KAILASH SHARMA",
        "DOB: 15/08/1989"
    ])

    files_aadhaar = {"file": ("aadhaar.png", aadhaar_img, "image/png")}
    data_aadhaar = {"document_type": "aadhaar"}
    up_aadhaar = requests.post(
        f"{BACKEND_URL}/api/v1/documents/upload",
        headers=headers_a,
        files=files_aadhaar,
        data=data_aadhaar
    )
    assert up_aadhaar.status_code == 201, f"Aadhaar upload failed: {up_aadhaar.text}"

    files_pan = {"file": ("pan.png", pan_img, "image/png")}
    data_pan = {"document_type": "pan"}
    up_pan = requests.post(
        f"{BACKEND_URL}/api/v1/documents/upload",
        headers=headers_a,
        files=files_pan,
        data=data_pan
    )
    assert up_pan.status_code == 201, f"PAN upload failed: {up_pan.text}"
    print("  [PASS] Both synthetic documents uploaded and processed via OCR.")

    # 5. Run conflict detection
    print("\n[TEST 5] Running conflict detection across uploaded documents...")
    det_resp = requests.post(f"{BACKEND_URL}/api/v1/conflicts/detect", headers=headers_a)
    assert det_resp.status_code == 200, f"Detection failed: {det_resp.text}"
    det_data = det_resp.json()
    assert det_data["total_documents_analyzed"] >= 2
    assert det_data["total_conflicts_detected"] >= 1
    print(f"  [PASS] Detection completed. Analyzed {det_data['total_documents_analyzed']} docs, detected {det_data['total_conflicts_detected']} discrepancies.")

    conflicts = det_data["conflicts"]
    first_conflict = conflicts[0]
    conflict_id = first_conflict["id"]

    # Verify no raw Aadhaar in conflict response
    for c in conflicts:
        assert "9876 5432" not in c["value_a"]
        assert "9876 5432" not in c["value_b"]
        assert "9876 5432" not in c["description"]
    print("  [PASS] Aadhaar Act compliance verified (no unmasked Aadhaar in conflict output).")

    # 6. List conflicts
    print("\n[TEST 6] Listing conflicts via GET /api/v1/conflicts...")
    list_resp = requests.get(f"{BACKEND_URL}/api/v1/conflicts", headers=headers_a)
    assert list_resp.status_code == 200
    list_json = list_resp.json()
    assert list_json["total"] >= 1
    print(f"  [PASS] Conflicts retrieved. Total: {list_json['total']}.")

    # 7. Get specific conflict by ID
    print(f"\n[TEST 7] Fetching conflict detail for {conflict_id}...")
    get_resp = requests.get(f"{BACKEND_URL}/api/v1/conflicts/{conflict_id}", headers=headers_a)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == conflict_id
    print("  [PASS] Conflict detail successfully retrieved.")

    # 8. Review status update
    print(f"\n[TEST 8] Updating review status to 'in_review'...")
    rev_resp = requests.patch(
        f"{BACKEND_URL}/api/v1/conflicts/{conflict_id}/review",
        headers=headers_a,
        json={"status": "in_review"}
    )
    assert rev_resp.status_code == 200
    assert rev_resp.json()["status"] == "in_review"
    print("  [PASS] Review status updated to 'in_review'.")

    # 9. Idempotency: re-running detection must not create duplicate records
    print("\n[TEST 9] Verifying idempotent detection execution...")
    rerun_resp = requests.post(f"{BACKEND_URL}/api/v1/conflicts/detect", headers=headers_a)
    assert rerun_resp.status_code == 200
    rerun_data = rerun_resp.json()
    assert rerun_data["new_conflicts_created"] == 0, f"Expected 0 new conflicts, got {rerun_data['new_conflicts_created']}"
    assert rerun_data["total_conflicts_detected"] == det_data["total_conflicts_detected"]
    print("  [PASS] Detection is strictly idempotent (0 duplicate records created on rerun).")

    # 10. Cross-Citizen Isolation
    print("\n[TEST 10] Testing RLS cross-citizen conflict isolation...")
    uid_b = f"cit_b_{uuid.uuid4().hex[:8]}"
    token_b = f"Bearer test_token_:{uid_b}:{uid_b}@test.in:Citizen Beta"
    headers_b = {"Authorization": token_b}
    requests.post(
        f"{BACKEND_URL}/api/v1/auth/provision",
        headers=headers_b,
        json={"email": f"{uid_b}@test.in", "full_name": "Citizen Beta"}
    )

    # Citizen B listing conflicts must NOT see Citizen A's conflicts
    list_b = requests.get(f"{BACKEND_URL}/api/v1/conflicts", headers=headers_b)
    assert list_b.status_code == 200
    assert list_b.json()["total"] == 0, f"Citizen B saw {list_b.json()['total']} conflicts, expected 0"

    # Citizen B cannot get Citizen A's conflict
    get_b = requests.get(f"{BACKEND_URL}/api/v1/conflicts/{conflict_id}", headers=headers_b)
    assert get_b.status_code == 404, f"Citizen B received {get_b.status_code}, expected 404"

    # Citizen B cannot patch Citizen A's conflict review status
    patch_b = requests.patch(
        f"{BACKEND_URL}/api/v1/conflicts/{conflict_id}/review",
        headers=headers_b,
        json={"status": "resolved"}
    )
    assert patch_b.status_code == 404, f"Citizen B received {patch_b.status_code}, expected 404"
    print("  [PASS] Cross-citizen conflict isolation strictly enforced by RLS.")

    print("\n==================================================")
    print("  ALL 10 CONFLICT DETECTION ENGINE TESTS PASSED!  ")
    print("==================================================")
    return 0

if __name__ == "__main__":
    sys.exit(run_tests())
