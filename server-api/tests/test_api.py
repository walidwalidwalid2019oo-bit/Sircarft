from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

import app as api


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SIRCARFT_API_TOKEN", "test-token-that-is-long-enough-for-local-tests")
    monkeypatch.setenv("SIRCARFT_DB_PATH", str(tmp_path / "sircarft.sqlite3"))
    monkeypatch.setenv("SIRCARFT_MAX_SERVERS", "2")
    with TestClient(api.app) as test_client:
        yield test_client


def auth(token="test-token-that-is-long-enough-for-local-tests"):
    return {"Authorization": f"Bearer {token}"}


def create_payload(name="Oakheart SMP"):
    return {"name": name, "edition": "Java", "mode": "Survival"}


def test_health_does_not_claim_provisioning_is_live(client):
    result = client.get("/health").json()
    assert result["status"] == "degraded"
    assert result["provisioning"] == "queue_only"
    assert "No Minecraft runtime worker" in result["note"]


def test_api_requires_bearer_token(client):
    response = client.get("/v1/servers")
    assert response.status_code == 401


def test_api_rejects_missing_server_token(monkeypatch, tmp_path):
    monkeypatch.delenv("SIRCARFT_API_TOKEN", raising=False)
    monkeypatch.setenv("SIRCARFT_DB_PATH", str(tmp_path / "db.sqlite3"))
    with TestClient(api.app) as test_client:
        assert test_client.get("/health").json()["status"] == "setup_required"
        assert test_client.get("/v1/servers").status_code == 503


def test_create_server_persists_a_queued_job_without_claiming_online(client):
    response = client.post(
        "/v1/servers",
        headers={**auth(), "Idempotency-Key": "request-create-0001"},
        json=create_payload(),
    )
    assert response.status_code == 202
    result = response.json()
    assert result["server"]["status"] == "queued"
    assert result["job"]["status"] == "queued"
    assert result["notice"].startswith("Request stored")
    assert client.get("/v1/servers", headers=auth()).json()["servers"][0]["id"] == result["server"]["id"]


def test_idempotency_replay_does_not_create_a_second_server(client):
    headers = {**auth(), "Idempotency-Key": "request-create-0002"}
    first = client.post("/v1/servers", headers=headers, json=create_payload()).json()
    second = client.post("/v1/servers", headers=headers, json=create_payload()).json()
    assert first["server"]["id"] == second["server"]["id"]
    assert second["replayed"] is True
    assert len(client.get("/v1/servers", headers=auth()).json()["servers"]) == 1


def test_reusing_idempotency_key_with_different_payload_is_rejected(client):
    headers = {**auth(), "Idempotency-Key": "request-create-0003"}
    client.post("/v1/servers", headers=headers, json=create_payload())
    response = client.post("/v1/servers", headers=headers, json=create_payload("Different world"))
    assert response.status_code == 409


def test_server_slot_quota_is_enforced_server_side(client, monkeypatch):
    monkeypatch.setenv("SIRCARFT_MAX_SERVERS", "1")
    client.post("/v1/servers", headers={**auth(), "Idempotency-Key": "request-create-0004"}, json=create_payload())
    response = client.post(
        "/v1/servers",
        headers={**auth(), "Idempotency-Key": "request-create-0005"},
        json=create_payload("Second world"),
    )
    assert response.status_code == 409


def test_unowned_or_unknown_server_is_not_disclosed(client):
    response = client.get("/v1/servers/not-a-real-id", headers=auth())
    assert response.status_code == 404


def test_create_requires_idempotency_key(client):
    response = client.post("/v1/servers", headers=auth(), json=create_payload())
    assert response.status_code == 400


def test_create_rejects_unlisted_runtime_settings(client):
    payload = {**create_payload(), "docker_image": "attacker/image", "memory_mb": 999999}
    response = client.post(
        "/v1/servers",
        headers={**auth(), "Idempotency-Key": "request-create-0006"},
        json=payload,
    )
    assert response.status_code == 422


def test_create_rejects_blank_world_name(client):
    response = client.post(
        "/v1/servers",
        headers={**auth(), "Idempotency-Key": "request-create-0007"},
        json=create_payload("   "),
    )
    assert response.status_code == 422

def test_non_ascii_bearer_token_is_rejected_as_unauthorized(client):
    response = client.get("/v1/servers", headers=auth("invalid-token-é"))
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid bearer token."
