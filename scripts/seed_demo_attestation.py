import httpx
import hashlib
import psycopg2

BASE_URL = "http://localhost:8000"

USER_TOKEN = "test_token_:ui_demo_user:user.demo@synthetic.test:Demo User"
ADMIN_TOKEN = "test_token_:ui_demo_admin:admin.demo@synthetic.test:Demo Admin"

def seed():
    # 1. Provision user profiles so they exist in DB
    httpx.post(
        f"{BASE_URL}/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {USER_TOKEN}", "Content-Type": "application/json"},
        json={"full_name": "Demo User"}
    )
    httpx.post(
        f"{BASE_URL}/api/v1/auth/provision",
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}", "Content-Type": "application/json"},
        json={"full_name": "Demo Administrator"}
    )

    # Set admin role for signing administrator
    conn = psycopg2.connect("postgresql://postgres:postgres_dev_password@localhost:5432/consolith")
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SET LOCAL app.current_user_role = 'admin';")
        cur.execute("UPDATE users SET role = 'admin' WHERE firebase_uid = 'ui_demo_admin';")
    conn.close()

    # 2. Get user profile to get exact user_id
    me_resp = httpx.get(
        f"{BASE_URL}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {USER_TOKEN}"}
    )
    user_id = me_resp.json().get("id")
    print("User ID:", user_id)

    # 3. Create synthetic test document fingerprint
    doc_bytes = b"SYNTHETIC AADHAAR CARD - USER DEMO - NUM: XXXX-XXXX-4772"
    doc_hash = hashlib.sha256(doc_bytes).hexdigest()

    # 4. Admin creates Platform Administrative Attestation
    attest_payload = {
        "document_type": "aadhaar",
        "document_fingerprint": doc_hash,
        "signing_purpose": "identity_discrepancy_verification",
        "expires_in_days": 365
    }

    resp = httpx.post(
        f"{BASE_URL}/api/v1/attestations?user_id={user_id}",
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}", "Content-Type": "application/json"},
        json=attest_payload
    )
    print("Platform Attestation creation:", resp.status_code, resp.json())

if __name__ == "__main__":
    seed()
