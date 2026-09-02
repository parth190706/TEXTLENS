"""
TextLens — API endpoint tests.
Uses FastAPI TestClient with an in-memory SQLite database.
"""
from __future__ import annotations

import io
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_upload_txt():
    content = b"Remote work was introduced in 2024. Productivity increased by 18%."
    resp = client.post(
        "/api/documents",
        files={"file": ("test.txt", io.BytesIO(content), "text/plain")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["file_type"] == "txt"
    assert data["status"] == "uploaded"
    return data["id"]


def test_upload_empty_file():
    resp = client.post(
        "/api/documents",
        files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
    )
    assert resp.status_code == 400


def test_upload_unsupported_type():
    resp = client.post(
        "/api/documents",
        files={"file": ("data.csv", io.BytesIO(b"a,b,c"), "text/csv")},
    )
    assert resp.status_code == 400


def test_list_documents():
    resp = client.get("/api/documents")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_document_not_found():
    resp = client.get("/api/documents/nonexistent-id")
    assert resp.status_code == 404


def test_status_not_found():
    resp = client.get("/api/documents/nonexistent-id/status")
    assert resp.status_code == 404
