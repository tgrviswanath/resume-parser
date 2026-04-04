# Azure Deployment Guide — Project 03 Resume Parser

---

## Azure Services for Resume Parsing

### 1. Ready-to-Use AI (No Model Needed)

| Service                              | What it does                                                                 | When to use                                        |
|--------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Azure AI Document Intelligence**   | Extract structured data from PDFs/DOCX — name, email, skills, dates         | Replace your spaCy NER + regex pipeline            |
| **Azure AI Language**                | Named entity recognition for PERSON, ORG, DATE entities                     | Enhance entity extraction accuracy                 |
| **Azure OpenAI Service**             | GPT-4 to extract and structure resume fields via prompt                      | When you need flexible, schema-free extraction     |

> **Azure AI Document Intelligence** (Form Recognizer) is the direct replacement for your PyMuPDF + spaCy pipeline. It handles PDF layout, tables, and key-value pairs out of the box.

### 2. Host Your Own Model (Keep Current Stack)

| Service                        | What it does                                                        | When to use                                           |
|--------------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **Azure Container Apps**       | Run your 3 Docker containers (frontend, backend, nlp-service)       | Best match for your current microservice architecture |
| **Azure App Service**          | Host FastAPI backend + nlp-service as web apps                      | Simple deployment, no containers needed               |
| **Azure Container Registry**   | Store your Docker images                                            | Used with Container Apps or AKS                       |

### 3. Train and Manage Your Model

| Service                        | What it does                                                              | When to use                                           |
|--------------------------------|---------------------------------------------------------------------------|-------------------------------------------------------|
| **Azure Machine Learning**     | Train custom NER models, track experiments, deploy endpoints              | When you need domain-specific entity extraction       |
| **Azure AI Language Studio**   | Train custom NER without code via UI                                      | Quick custom entity training on resume data           |

### 4. Frontend Hosting

| Service                   | What it does                                                               |
|---------------------------|----------------------------------------------------------------------------|
| **Azure Static Web Apps** | Host your React frontend — free tier available, auto CI/CD from GitHub     |
| **Azure CDN**             | Serve static assets globally with low latency                              |

### 5. Supporting Services

| Service                       | Purpose                                                                  |
|-------------------------------|--------------------------------------------------------------------------|
| **Azure Blob Storage**        | Store uploaded resume files and parsed results                           |
| **Azure Key Vault**           | Store API keys and connection strings instead of .env files              |
| **Azure Monitor + App Insights** | Track parsing latency, error rates, request volume                    |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Azure Static Web Apps — React Frontend                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  Azure Container Apps — Backend (FastAPI :8000)             │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ Container Apps    │    │ Azure AI Document Intelligence     │
│ NLP Service :8001 │    │ + Azure AI Language NER            │
│ spaCy + PyMuPDF   │    │ No model maintenance needed        │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
az login
az group create --name rg-resume-parser --location uksouth
az extension add --name containerapp --upgrade
```

---

## Step 1 — Create Container Registry and Push Images

```bash
az acr create --resource-group rg-resume-parser --name resumeparseracr --sku Basic --admin-enabled true
az acr login --name resumeparseracr
ACR=resumeparseracr.azurecr.io
docker build -f docker/Dockerfile.nlp-service -t $ACR/nlp-service:latest ./nlp-service
docker push $ACR/nlp-service:latest
docker build -f docker/Dockerfile.backend -t $ACR/backend:latest ./backend
docker push $ACR/backend:latest
```

---

## Step 2 — Create Blob Storage for Resume Files

```bash
az storage account create --name resumefiles --resource-group rg-resume-parser --sku Standard_LRS
az storage container create --name resumes --account-name resumefiles
az storage container create --name parsed --account-name resumefiles
```

---

## Step 3 — Deploy Container Apps

```bash
az containerapp env create --name resume-env --resource-group rg-resume-parser --location uksouth

az containerapp create \
  --name nlp-service --resource-group rg-resume-parser \
  --environment resume-env --image $ACR/nlp-service:latest \
  --registry-server $ACR --target-port 8001 --ingress internal \
  --min-replicas 1 --max-replicas 3 --cpu 0.5 --memory 1.0Gi

az containerapp create \
  --name backend --resource-group rg-resume-parser \
  --environment resume-env --image $ACR/backend:latest \
  --registry-server $ACR --target-port 8000 --ingress external \
  --min-replicas 1 --max-replicas 5 --cpu 0.5 --memory 1.0Gi \
  --env-vars NLP_SERVICE_URL=http://nlp-service:8001
```

---

## Option B — Use Azure AI Document Intelligence

```bash
az cognitiveservices account create \
  --name resume-doc-intelligence \
  --resource-group rg-resume-parser \
  --kind FormRecognizer \
  --sku S0 \
  --location uksouth \
  --yes
```

```python
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

client = DocumentAnalysisClient(
    endpoint=os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT"),
    credential=AzureKeyCredential(os.getenv("AZURE_DOC_INTELLIGENCE_KEY"))
)

def parse_resume(file_bytes: bytes) -> dict:
    poller = client.begin_analyze_document("prebuilt-document", file_bytes)
    result = poller.result()
    # Extract key-value pairs, tables, and entities
    fields = {kv.key.content: kv.value.content for kv in result.key_value_pairs if kv.value}
    return fields
```

Add to requirements.txt: `azure-ai-formrecognizer>=3.3.0`

---

## CI/CD — GitHub Actions

```yaml
name: Deploy to Azure
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      - run: az acr login --name resumeparseracr
      - run: |
          docker build -f docker/Dockerfile.backend -t resumeparseracr.azurecr.io/backend:${{ github.sha }} ./backend
          docker push resumeparseracr.azurecr.io/backend:${{ github.sha }}
          az containerapp update --name backend --resource-group rg-resume-parser \
            --image resumeparseracr.azurecr.io/backend:${{ github.sha }}
```

---

## Estimated Monthly Cost

| Service                  | Tier      | Est. Cost         |
|--------------------------|-----------|-------------------|
| Container Apps (backend) | 0.5 vCPU  | ~$10–15/month     |
| Container Apps (nlp-svc) | 0.5 vCPU  | ~$10–15/month     |
| Container Registry       | Basic     | ~$5/month         |
| Static Web Apps          | Free      | $0                |
| Blob Storage             | LRS       | ~$1/month         |
| Doc Intelligence         | S0 tier   | Pay per page      |
| **Total (Option A)**     |           | **~$26–36/month** |
| **Total (Option B)**     |           | **~$16–21/month** |

For exact estimates → https://calculator.azure.com

---

## Teardown

```bash
az group delete --name rg-resume-parser --yes --no-wait
```
