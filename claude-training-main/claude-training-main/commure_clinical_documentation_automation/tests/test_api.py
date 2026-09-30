import pytest
from fastapi.testclient import TestClient

import main
from llm_client import ClaudeClient


@pytest.fixture()
def client():
    # Force mock mode so the API tests never hit the network, and reset
    # pipeline state between tests since `main.pipeline` is a module global.
    main.pipeline = main.MultiTenantPipeline(llm_client=ClaudeClient(force_mock=True))
    main.app.dependency_overrides.clear()
    return TestClient(main.app)


def test_register_tenant_and_set_template(client):
    tenant_resp = client.post(
        "/v1/tenants",
        json={"health_system_name": "Test Health", "ehr_vendor": "epic", "data_residency_region": "us-east"},
    )
    assert tenant_resp.status_code == 200
    tenant_id = tenant_resp.json()["id"]

    template_resp = client.put(
        f"/v1/tenants/{tenant_id}/templates/primary_care",
        json={"section_schema": ["subjective", "plan"]},
    )
    assert template_resp.status_code == 200
    assert template_resp.json()["section_schema"] == ["subjective", "plan"]


def test_encounter_to_note_to_deliver_flow(client):
    tenant_id = client.post(
        "/v1/tenants",
        json={"health_system_name": "Test Health", "ehr_vendor": "cerner", "data_residency_region": "us-central"},
    ).json()["id"]
    client.put(f"/v1/tenants/{tenant_id}/templates/cardiology", json={"section_schema": ["history", "plan"]})

    encounter_id = client.post(
        f"/v1/tenants/{tenant_id}/encounters", json={"clinician_id": "dr-osei", "specialty": "cardiology"}
    ).json()["id"]

    audio_resp = client.post(
        f"/v1/tenants/{tenant_id}/encounters/{encounter_id}/audio",
        json={"audio_text": "Patient reports palpitations."},
    )
    assert audio_resp.status_code == 200
    assert audio_resp.json()["status"] == "delivered"

    note_resp = client.get(f"/v1/tenants/{tenant_id}/encounters/{encounter_id}/note")
    note = note_resp.json()["note"]
    assert set(note["content_sections"].keys()) == {"history", "plan"}
    assert note["ehr_document_id"].startswith("cerner-note-")

    deliver_resp = client.post(f"/v1/tenants/{tenant_id}/encounters/{encounter_id}/deliver")
    assert deliver_resp.status_code == 200
    assert deliver_resp.json()["ehr_document_id"] == note["ehr_document_id"]


def test_metrics_endpoint(client):
    tenant_id = client.post(
        "/v1/tenants",
        json={"health_system_name": "Test Health", "ehr_vendor": "athenahealth", "data_residency_region": "us-west"},
    ).json()["id"]
    encounter_id = client.post(
        f"/v1/tenants/{tenant_id}/encounters", json={"clinician_id": "dr-patel", "specialty": "pediatrics"}
    ).json()["id"]
    client.post(f"/v1/tenants/{tenant_id}/encounters/{encounter_id}/audio", json={"audio_text": "Well child visit."})

    metrics_resp = client.get(f"/v1/tenants/{tenant_id}/metrics/throughput")
    assert metrics_resp.status_code == 200
    body = metrics_resp.json()
    assert body["encounters_delivered"] == 1
    assert body["notes_generated"] == 1


def test_unknown_tenant_returns_404(client):
    resp = client.get("/v1/tenants/does-not-exist/metrics/throughput")
    assert resp.status_code == 404
