import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../nlp-service"))

from app.core.extractor import (
    extract_email, extract_phone, extract_skills, extract_name
)

SAMPLE = """
John Smith
john.smith@example.com
+1 (555) 123-4567
linkedin.com/in/johnsmith
github.com/johnsmith

Skills: Python, FastAPI, Docker, Machine Learning, PostgreSQL
"""


def test_extract_email():
    assert extract_email(SAMPLE) == "john.smith@example.com"


def test_extract_phone():
    assert "+1" in extract_phone(SAMPLE) or "555" in extract_phone(SAMPLE)


def test_extract_skills():
    skills = extract_skills(SAMPLE)
    assert "python" in skills
    assert "docker" in skills
    assert "machine learning" in skills


def test_extract_name():
    name = extract_name(SAMPLE)
    assert isinstance(name, str)
