import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

MOCK_RESULT = {
    "name": "John Smith",
    "email": "john@example.com",
    "phone": "+1 555 123 4567",
    "linkedin": "linkedin.com/in/johnsmith",
    "github": "github.com/johnsmith",
    "skills": ["python", "docker"],
    "education": ["B.Sc Computer Science"],
    "experience": [{"start": "2020", "end": "Present"}],
    "word_count": 150,
}


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@patch("app.core.service.parse_resume", new_callable=AsyncMock, return_value=MOCK_RESULT)
def test_parse_endpoint(mock_parse):
    dummy_pdf = b"%PDF-1.4 dummy content"
    res = client.post(
        "/api/v1/parse",
        files={"file": ("resume.pdf", dummy_pdf, "application/pdf")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "John Smith"
    assert "python" in data["skills"]
