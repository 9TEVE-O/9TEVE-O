"""End-to-end integration tests for the Able to Answer API."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from able_to_answer.core.storage import SqliteStore
from able_to_answer.api.main import app


@pytest.fixture()
def client(tmp_path):
    """Create a test client backed by a temporary in-memory-like SQLite db."""
    db_path = str(tmp_path / "test.sqlite3")
    test_store = SqliteStore(db_path)
    # Patch the module-level store used by the app
    import able_to_answer.api.main as main_module
    original_store = main_module.store
    main_module.store = test_store
    yield TestClient(app)
    main_module.store = original_store


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ingest_text(client):
    resp = client.post(
        "/ingest/text",
        json={"source_name": "demo", "text": "This is a demo document about council compliance and audit trails."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["document_id"].startswith("doc_")
    assert data["chunk_count"] >= 1
    assert len(data["document_sha256"]) == 64


def test_ingest_empty_text_raises(client):
    resp = client.post("/ingest/text", json={"text": "   "})
    assert resp.status_code == 422


def test_ask_flow(client):
    # Ingest
    ingest_resp = client.post(
        "/ingest/text",
        json={
            "source_name": "audit-demo",
            "text": (
                "This document describes council compliance procedures. "
                "It covers risk assessment, evidence collection, and audit trails. "
                "The governance framework requires that all decisions are logged."
            ),
        },
    )
    assert ingest_resp.status_code == 200
    doc_id = ingest_resp.json()["document_id"]

    # Ask
    ask_resp = client.post(
        "/ask",
        json={"document_id": doc_id, "question": "What does it say about audit trails?"},
    )
    assert ask_resp.status_code == 200
    data = ask_resp.json()
    assert data["document_id"] == doc_id
    assert data["answer"]
    assert isinstance(data["citations"], list)
    assert data["audit_id"].startswith("audit_")
    assert "created_at" in data["audit_pack"]


def test_ask_document_not_found(client):
    resp = client.post(
        "/ask",
        json={"document_id": "doc_doesnotexist", "question": "anything"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "document_not_found"


def test_ingest_file(client):
    content = b"Council governance report: risk management and compliance audit."
    resp = client.post(
        "/ingest/file",
        files={"file": ("report.txt", content, "text/plain")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["document_id"].startswith("doc_")


def test_list_documents_empty(client):
    resp = client.get("/documents")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_documents(client):
    client.post(
        "/ingest/text",
        json={"source_name": "list-test", "text": "Document listing test content."},
    )
    resp = client.get("/documents")
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) == 1
    doc = docs[0]
    assert doc["document_id"].startswith("doc_")
    assert doc["source_name"] == "list-test"
    assert doc["text_len"] > 0
    assert len(doc["sha256"]) == 64


def test_get_audit(client):
    # Ingest + ask to create an audit record
    ingest_resp = client.post(
        "/ingest/text",
        json={"source_name": "audit-read-test", "text": "Compliance framework documentation."},
    )
    doc_id = ingest_resp.json()["document_id"]
    ask_resp = client.post(
        "/ask",
        json={"document_id": doc_id, "question": "What is the compliance framework?"},
    )
    audit_id = ask_resp.json()["audit_id"]

    # Retrieve the audit record
    resp = client.get(f"/audits/{audit_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["audit_id"] == audit_id
    assert data["document_id"] == doc_id
    assert data["question"] == "What is the compliance framework?"
    assert data["answer"]
    assert isinstance(data["citations"], list)
    assert "created_at" in data["audit_pack"]


def test_get_audit_not_found(client):
    resp = client.get("/audits/audit_doesnotexist")
    assert resp.status_code == 404
    assert resp.json()["error"] == "audit_not_found"
