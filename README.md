# Project 03 - Resume Parser

Microservice NLP system that extracts structured data from PDF/DOCX resumes.

## Architecture

```
Frontend :3000  →  Backend :8000  →  NLP Service :8001
  React            FastAPI            FastAPI + spaCy
  File upload      File proxy         PDF/DOCX parsing
  Results UI       CORS + routing     Entity extraction
```

## What Gets Extracted

| Field | Method |
|-------|--------|
| Name | spaCy NER (PERSON entity) |
| Email | regex |
| Phone | regex |
| LinkedIn / GitHub | regex |
| Skills | PhraseMatcher against skills DB |
| Education | regex + spaCy ORG entities |
| Experience | date range regex |

## Local Run

```bash
# Terminal 1 - NLP Service
cd nlp-service
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --reload --port 8001

# Terminal 2 - Backend
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 3 - Frontend
cd frontend
npm install
npm start
```

- Frontend → http://localhost:3000
- Backend API docs → http://localhost:8000/docs
- NLP Service docs → http://localhost:8001/docs

## Docker (Full Stack)

```bash
docker-compose up --build
```

## Run Tests

```bash
# NLP service tests
pip install -r nlp-service/requirements.txt
python -m spacy download en_core_web_sm
pytest tests/nlp-service/ -v

# Backend tests
pip install -r backend/requirements.txt pytest pytest-asyncio httpx
pytest tests/backend/ -v
```

## Tools Used

| Layer | Tools |
|-------|-------|
| NLP Service | spaCy, PyMuPDF, python-docx, regex |
| Backend | FastAPI, httpx, pydantic-settings |
| Frontend | React, MUI, Recharts, axios |
| DevOps | Docker, GitHub Actions |
