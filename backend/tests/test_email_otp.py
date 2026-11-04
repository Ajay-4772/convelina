import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import EmailOTP
from app.core.database import get_db

client = TestClient(app)

def test_otp_send_and_verify_flow():
    # 1. Invalid email format rejected
    res = client.post("/api/v1/auth/otp/send", json={"email": "invalid-email"})
    assert res.status_code == 400

    # 2. Valid email dispatches OTP (timestamped to ensure test isolation across rapid runs)
    test_email = f"citizen_verify_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}@gmail.com"
    res = client.post("/api/v1/auth/otp/send", json={"email": test_email})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "sent" in data["message"].lower() or "generated" in data["message"].lower()

    # 3. Resend cooldown rejected (immediate retry)
    res_cooldown = client.post("/api/v1/auth/otp/send", json={"email": test_email})
    assert res_cooldown.status_code == 429
    assert "Please wait" in res_cooldown.json()["detail"]

    # 4. Incorrect OTP rejected
    res_bad = client.post("/api/v1/auth/otp/verify", json={"email": test_email, "otp_code": "000000"})
    assert res_bad.status_code == 200
    assert res_bad.json()["verified"] is False

    # 5. Simulated/Dev code verified
    res_sim = client.post("/api/v1/auth/otp/verify", json={"email": test_email, "otp_code": "123456"})
    assert res_sim.status_code == 200
    assert res_sim.json()["verified"] is True
    assert res_sim.json()["verification_token"] is not None
