# GCP Deployment Guide — Project 03 Resume Parser

---

## GCP Services for Resume Parsing

### 1. Ready-to-Use AI (No Model Needed)

| Service                              | What it does                                                                 | When to use                                        |
|--------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Cloud Document AI**                | Extract structured data from PDFs — name, email, skills, dates, tables      | Replace your PyMuPDF + spaCy pipeline              |
| **Cloud Natural Language API**       | Named entity recognition for PERSON, ORG, DATE, LOCATION                    | Enhance entity extraction from extracted text      |
| **Vertex AI Gemini**                 | Gemini Pro to extract and structure resume fields via prompt                 | When you need flexible, schema-free extraction     |

> **Cloud Document AI** is the direct replacement for your PyMuPDF + spaCy pipeline. It handles PDF layout, tables, and key-value pairs with pre-trained and custom processors.

### 2. Host Your Own Model (Keep Current Stack)

| Service                    | What it does                                                        | When to use                                           |
|----------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **Cloud Run**              | Run backend + nlp-service containers — serverless, scales to zero   | Best match for your current microservice architecture |
| **Google Kubernetes Engine** | Full Kubernetes for your 3 services                               | When you need auto-scaling at production scale        |
| **Artifact Registry**      | Store your Docker images                                            | Used with Cloud Run or GKE                            |

### 3. Train and Manage Your Model

| Service                      | What it does                                                              | When to use                                           |
|------------------------------|---------------------------------------------------------------------------|-------------------------------------------------------|
| **Vertex AI**                | Train custom NER models, track experiments, deploy managed endpoints      | When you need domain-specific entity extraction       |
| **Document AI Custom**       | Train custom document processors for resume-specific fields               | Quick custom extraction training on resume data       |

### 4. Frontend Hosting

| Service                    | What it does                                                              |
|----------------------------|---------------------------------------------------------------------------|
| **Firebase Hosting**       | Host your React frontend — free tier, auto CI/CD from GitHub              |
| **Cloud CDN**              | Serve static assets globally with low latency                             |

### 5. Supporting Services

| Service                        | Purpose                                                                   |
|--------------------------------|---------------------------------------------------------------------------|
| **Cloud Storage**              | Store uploaded resume files and parsed JSON results                       |
| **Secret Manager**             | Store API keys and connection strings instead of .env files               |
| **Cloud Monitoring + Logging** | Track parsing latency, error rates, request volume                        |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Firebase Hosting — React Frontend                          │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  Cloud Run — Backend (FastAPI :8000)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal HTTPS
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ Cloud Run         │    │ Cloud Document AI                  │
│ NLP Service :8001 │    │ + Cloud Natural Language NER       │
│ spaCy + PyMuPDF   │    │ No model maintenance needed        │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
gcloud auth login
gcloud projects create resumeparser-project --name="Resume Parser"
gcloud config set project resumeparser-project
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com language.googleapis.com \
  storage.googleapis.com documentai.googleapis.com cloudbuild.googleapis.com
```

---

## Step 1 — Create Artifact Registry and Push Images

```bash
GCP_REGION=europe-west2
gcloud artifacts repositories create resumeparser-repo \
  --repository-format=docker --location=$GCP_REGION
gcloud auth configure-docker $GCP_REGION-docker.pkg.dev
AR=$GCP_REGION-docker.pkg.dev/resumeparser-project/resumeparser-repo
docker build -f docker/Dockerfile.nlp-service -t $AR/nlp-service:latest ./nlp-service
docker push $AR/nlp-service:latest
docker build -f docker/Dockerfile.backend -t $AR/backend:latest ./backend
docker push $AR/backend:latest
```

---

## Step 2 — Create Cloud Storage for Resume Files

```bash
gsutil mb -l $GCP_REGION gs://resume-files-resumeparser-project
gsutil cors set cors.json gs://resume-files-resumeparser-project
```

---

## Step 3 — Deploy to Cloud Run

```bash
gcloud run deploy nlp-service \
  --image $AR/nlp-service:latest --region $GCP_REGION \
  --port 8001 --no-allow-unauthenticated \
  --min-instances 1 --max-instances 3 --memory 2Gi --cpu 1

NLP_URL=$(gcloud run services describe nlp-service --region $GCP_REGION --format "value(status.url)")

gcloud run deploy backend \
  --image $AR/backend:latest --region $GCP_REGION \
  --port 8000 --allow-unauthenticated \
  --min-instances 1 --max-instances 5 --memory 1Gi --cpu 1 \
  --set-env-vars NLP_SERVICE_URL=$NLP_URL
```

---

## Option B — Use Cloud Document AI

```bash
# Create Document AI processor
gcloud documentai processors create \
  --location=eu \
  --display-name="Resume Parser" \
  --type=FORM_PARSER_PROCESSOR
```

```python
from google.cloud import documentai_v1 as documentai

client = documentai.DocumentProcessorServiceClient()

def parse_resume(file_bytes: bytes, mime_type: str = "application/pdf") -> dict:
    processor_name = "projects/<project>/locations/eu/processors/<processor-id>"
    raw_document = documentai.RawDocument(content=file_bytes, mime_type=mime_type)
    request = documentai.ProcessRequest(name=processor_name, raw_document=raw_document)
    result = client.process_document(request=request)
    document = result.document
    fields = {entity.type_: entity.mention_text for entity in document.entities}
    return {"text": document.text, "fields": fields}
```

Add to requirements.txt: `google-cloud-documentai>=2.20.0`

---

## CI/CD — GitHub Actions

```yaml
name: Deploy to GCP
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      - uses: google-github-actions/setup-gcloud@v2
      - run: gcloud auth configure-docker europe-west2-docker.pkg.dev
      - run: |
          docker build -f docker/Dockerfile.backend \
            -t europe-west2-docker.pkg.dev/${{ secrets.GCP_PROJECT }}/resumeparser-repo/backend:${{ github.sha }} ./backend
          docker push europe-west2-docker.pkg.dev/${{ secrets.GCP_PROJECT }}/resumeparser-repo/backend:${{ github.sha }}
          gcloud run deploy backend \
            --image europe-west2-docker.pkg.dev/${{ secrets.GCP_PROJECT }}/resumeparser-repo/backend:${{ github.sha }} \
            --region europe-west2 --platform managed
```

---

## Estimated Monthly Cost

| Service                    | Tier                  | Est. Cost          |
|----------------------------|-----------------------|--------------------|
| Cloud Run (backend)        | 1 vCPU / 1 GB         | ~$10–15/month      |
| Cloud Run (nlp-service)    | 1 vCPU / 2 GB         | ~$12–18/month      |
| Artifact Registry          | Storage               | ~$1–2/month        |
| Firebase Hosting           | Free tier             | $0                 |
| Cloud Storage              | Standard              | ~$1/month          |
| Cloud Document AI          | Pay per page          | ~$1.50/1000 pages  |
| **Total (Option A)**       |                       | **~$24–36/month**  |
| **Total (Option B)**       |                       | **~$14–20/month**  |

For exact estimates → https://cloud.google.com/products/calculator

---

## Teardown

```bash
gcloud run services delete backend --region $GCP_REGION --quiet
gcloud run services delete nlp-service --region $GCP_REGION --quiet
gcloud artifacts repositories delete resumeparser-repo --location=$GCP_REGION --quiet
gsutil rm -r gs://resume-files-resumeparser-project
gcloud projects delete resumeparser-project
```
