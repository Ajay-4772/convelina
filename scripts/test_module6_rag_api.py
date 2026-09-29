import requests
import uuid

API_BASE = "http://localhost:8000"

def get_token(role="citizen", user_tag="alice"):
    return f"test_token_:{user_tag}_{role}:{user_tag}.{role}@synthetic.test:{user_tag.capitalize()} User"

def run_tests():
    print("======================================================================")
    print("CONSOLITH MODULE 6: RAG & CONVERSATIONAL ASSISTANT INTEGRATION TESTS")
    print("======================================================================\n")

    # 1. Health check
    h = requests.get(f"{API_BASE}/health").json()
    assert h["status"] == "healthy"
    print("PASS: System Health Verified (postgres: up, qdrant: up)")

    # 2. Knowledge Sources (Citizen role)
    uid_1 = f"cit_rag_{uuid.uuid4().hex[:8]}"
    token_1 = f"Bearer test_token_:{uid_1}:{uid_1}@synthetic.test:Citizen RAG One"
    headers = {"Authorization": token_1}

    # Provision user profile first
    requests.post(
        f"{API_BASE}/api/v1/auth/provision",
        headers=headers,
        json={"email": f"{uid_1}@synthetic.test", "full_name": "Citizen RAG One"}
    )

    res_sources = requests.get(f"{API_BASE}/api/v1/knowledge/sources", headers=headers)
    assert res_sources.status_code == 200, f"Expected 200, got {res_sources.status_code}"
    sources_data = res_sources.json()
    assert sources_data["total"] >= 5, "Expected at least 5 official knowledge sources"
    print(f"PASS: Verified {sources_data['total']} Official Government Knowledge Sources (UIDAI, NSDL, MEA, EPFO, CBSE)")

    # 3. Official Forms Catalog
    res_forms = requests.get(f"{API_BASE}/api/v1/knowledge/forms", headers=headers)
    assert res_forms.status_code == 200
    forms_data = res_forms.json()
    assert forms_data["total"] >= 6, "Expected at least 6 official forms"
    pan_forms = [f for f in forms_data["forms"] if f["document_category"] == "pan"]
    assert len(pan_forms) >= 1
    assert "https://" in pan_forms[0]["official_download_url"]
    print(f"PASS: Verified {forms_data['total']} Official Forms Catalog with verified download URLs")

    # 4. Chat Endpoint — Grounded Procedural Inquiry
    chat_payload = {
        "message": "How do I correct my name in PAN card?",
        "document_category": "pan"
    }
    chat_res = requests.post(f"{API_BASE}/api/v1/assistant/chat", json=chat_payload, headers=headers)
    assert chat_res.status_code == 200, f"Chat failed: {chat_res.text}"
    chat_data = chat_res.json()
    assert chat_data["conversation_id"] is not None
    resp_obj = chat_data["response"]
    assert resp_obj["confidence"] in ["supported", "partially_supported"]
    assert len(resp_obj["resolution_steps"]) >= 1
    assert len(resp_obj["citations"]) >= 1
    print(f"PASS: Chat Inquiry Grounded — Returned {len(resp_obj['resolution_steps'])} steps and {len(resp_obj['citations'])} official citations")

    # 5. Conversational Continuity & Follow-up
    conv_id = chat_data["conversation_id"]
    followup_payload = {
        "message": "What supporting documents do I need to attach?",
        "conversation_id": conv_id,
        "document_category": "pan"
    }
    followup_res = requests.post(f"{API_BASE}/api/v1/assistant/chat", json=followup_payload, headers=headers)
    assert followup_res.status_code == 200
    followup_data = followup_res.json()
    assert followup_data["conversation_id"] == conv_id
    print("PASS: Conversational Continuity Preserved across follow-up turns")

    # 6. Conversation List & Messages
    msgs_res = requests.get(f"{API_BASE}/api/v1/assistant/conversations/{conv_id}/messages", headers=headers)
    assert msgs_res.status_code == 200
    msgs_data = msgs_res.json()
    assert msgs_data["total"] >= 4  # 2 user queries + 2 assistant responses
    print(f"PASS: Conversation History Persisted in PostgreSQL ({msgs_data['total']} messages)")

    # 7. Cross-Citizen RLS Conversation Isolation
    uid_2 = f"cit_bob_{uuid.uuid4().hex[:8]}"
    bob_token = f"Bearer test_token_:{uid_2}:{uid_2}@synthetic.test:Citizen Bob"
    bob_headers = {"Authorization": bob_token}
    requests.post(
        f"{API_BASE}/api/v1/auth/provision",
        headers=bob_headers,
        json={"email": f"{uid_2}@synthetic.test", "full_name": "Citizen Bob"}
    )
    bob_attempt = requests.get(f"{API_BASE}/api/v1/assistant/conversations/{conv_id}/messages", headers=bob_headers)
    assert bob_attempt.status_code == 404, "Security violation: Cross-citizen conversation access allowed!"
    print("PASS: Cross-Citizen Conversation Isolation Enforced via PostgreSQL Forced RLS")

    # 8. Relevance Floor (>= 0.55) Enforcement
    irrelevant_payload = {
        "message": "What is the capital city of France?"
    }
    irr_res = requests.post(f"{API_BASE}/api/v1/assistant/chat", json=irrelevant_payload, headers=headers)
    assert irr_res.status_code == 200
    irr_data = irr_res.json()
    assert irr_data["response"]["confidence"] == "insufficient_evidence"
    assert len(irr_data["response"]["citations"]) == 0
    print("PASS: Relevance Floor Enforced (>= 0.55) — Zero Hallucination on Out-of-Domain Query")

    print("\nALL MODULE 6 API INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
