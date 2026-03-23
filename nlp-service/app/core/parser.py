import fitz  # PyMuPDF
import docx
import io
from app.core.extractor import (
    extract_name, extract_email, extract_phone,
    extract_links, extract_skills, extract_education, extract_experience,
)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(para.text for para in doc.paragraphs)


def parse_resume(file_bytes: bytes, filename: str) -> dict:
    if filename.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif filename.lower().endswith(".docx"):
        text = extract_text_from_docx(file_bytes)
    else:
        text = file_bytes.decode("utf-8", errors="ignore")

    links = extract_links(text)
    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "linkedin": links["linkedin"],
        "github": links["github"],
        "skills": extract_skills(text),
        "education": extract_education(text),
        "experience": extract_experience(text),
        "word_count": len(text.split()),
    }
