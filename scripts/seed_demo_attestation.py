import httpx
import hashlib

BASE_URL = "http://localhost:8000"

CITIZEN_TOKEN = "test_token_:ui_demo_citizen:citizen.demo@synthetic.test:CITIZEN User"
OFFICER_TOKEN = "test_token_:ui_demo_officer:officer.demo@synthetic.test:OFFICER User"

def seed():
    # 1. Provision user profiles so they exist in DB
    httpx.post(
        f"{BASE_URL}/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {CITIZEN_TOKEN}", "Content-Type": "application/json"},
        json={"full_name": "Citizen Demo User"}
    )
    httpx.post(
        f"{BASE_URL}/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {OFFICER_TOKEN}", "Content-Type": "application/json"},
        json={"full_name": "Officer Demo User"}
    )

    # 2. Get citizen profile to get exact citizen_id
    me_resp = httpx.get(
        f"{BASE_URL}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {CITIZEN_TOKEN}"}
    )
    citizen_id = me_resp.json().get("id")
    print("Citizen ID:", citizen_id)

    # 3. Create synthetic test document fingerprint
    doc_bytes = b"SYNTHETIC AADHAAR CARD - CITIZEN DEMO USER - NUM: XXXX-XXXX-4772"
    doc_hash = hashlib.sha256(doc_bytes).hexdigest()

    # 4. Officer creates official attestation
    attest_payload = {
        "document_type": "aadhaar",
        "document_fingerprint": doc_hash,
        "signing_purpose": "identity_discrepancy_verification",
        "expires_in_days": 365
    }

    resp = httpx.post(
        f"{BASE_URL}/api/v1/attestations?citizen_id={citizen_id}",
        headers={"Authorization": f"Bearer {OFFICER_TOKEN}", "Content-Type": "application/json"},
        json=attest_payload
    )
    print("Attestation creation:", resp.status_code, resp.json())

if __name__ == "__main__":
    seed()
