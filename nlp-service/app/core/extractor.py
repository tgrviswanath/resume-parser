import re
import spacy

# python -m spacy download en_core_web_sm
_nlp = None


def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


# Common tech skills list for PhraseMatcher
SKILLS_DB = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "react", "angular", "vue", "node.js", "fastapi", "django", "flask",
    "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "scikit-learn", "keras",
    "aws", "azure", "gcp", "docker", "kubernetes", "git", "ci/cd",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "pandas", "numpy", "matplotlib", "seaborn", "spark", "kafka",
    "rest api", "graphql", "microservices", "agile", "scrum",
]

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(\+?\d[\d\s\-().]{7,}\d)")
LINKEDIN_RE = re.compile(r"linkedin\.com/in/[\w\-]+", re.IGNORECASE)
GITHUB_RE = re.compile(r"github\.com/[\w\-]+", re.IGNORECASE)


def extract_name(text: str) -> str:
    nlp = get_nlp()
    doc = nlp(text[:1000])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text.strip()
    # fallback: first non-empty short line
    for line in text.splitlines()[:5]:
        line = line.strip()
        if line and 2 <= len(line.split()) <= 4 and not any(c.isdigit() for c in line):
            return line
    return ""


def extract_email(text: str) -> str:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    match = PHONE_RE.search(text)
    return match.group(0).strip() if match else ""


def extract_links(text: str) -> dict:
    linkedin = LINKEDIN_RE.search(text)
    github = GITHUB_RE.search(text)
    return {
        "linkedin": linkedin.group(0) if linkedin else "",
        "github": github.group(0) if github else "",
    }


def extract_skills(text: str) -> list[str]:
    text_lower = text.lower()
    found = [skill for skill in SKILLS_DB if skill in text_lower]
    return sorted(set(found))


def extract_education(text: str) -> list[str]:
    nlp = get_nlp()
    doc = nlp(text)
    degrees = re.findall(
        r"\b(B\.?Sc|B\.?Tech|M\.?Sc|M\.?Tech|MBA|Ph\.?D|Bachelor|Master|Doctorate)[^\n,]*",
        text, re.IGNORECASE
    )
    orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    return list(set(degrees + orgs[:5]))  # cap orgs to avoid noise


def extract_experience(text: str) -> list[dict]:
    """Extract date ranges as experience entries."""
    date_range_re = re.compile(
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4})"
        r"\s*[-–to]+\s*"
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4}|Present|Current|Now)",
        re.IGNORECASE,
    )
    matches = date_range_re.findall(text)
    return [{"start": s.strip(), "end": e.strip()} for s, e in matches]
