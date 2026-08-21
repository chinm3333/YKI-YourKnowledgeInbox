from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app import app
from services.store import init_db

@pytest.fixture
def client(tmp_path, monkeypatch):
    from config import settings
    settings.sqlite_path = tmp_path / "app.db"
    init_db()
    monkeypatch.setattr(
        "routers.ingest.upsert_chunks",
        lambda item_id, chunks, metadata: len(chunks),
    )
    monkeypatch.setattr("routers.ingest.delete_chunks", lambda item_id: None)
    monkeypatch.setattr("routers.items.delete_chunks", lambda item_id: None)
    monkeypatch.setattr("routers.query.query_chunks", lambda question, top_k: [])
    with TestClient(app) as test_client:
        yield test_client

def test_ingest_note_returns_201(client):
    response = client.post(
        "/ingest",
        json={"type": "note", "content": "Turium stores notes and answers from retrieved chunks."},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "note"
    assert body["chunk_count"] >= 1
    listed = client.get("/items")
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1

def test_invalid_url_returns_400(client):
    response = client.post("/ingest", json={"type": "url", "content": "not-a-url"})
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "validation_error"
    assert "http" in body["detail"].lower()

def test_empty_query_says_unknown(client):
    response = client.post("/query", json={"question": "What did I save about Turium?"})
    assert response.status_code == 200
    body = response.json()
    assert body["sources"] == []
    assert "don't know" in body["answer"].lower()

def test_delete_item(client):
    created = client.post("/ingest", json={"type": "note", "content": "delete me please"})
    item_id = created.json()["id"]
    deleted = client.delete(f"/items/{item_id}")
    assert deleted.status_code == 204
    listed = client.get("/items").json()["items"]
    assert listed == []

def test_delete_missing_item(client):
    response = client.delete(f"/items/{uuid4()}")
    assert response.status_code == 404