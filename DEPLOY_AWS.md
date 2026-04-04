# AWS Deployment Guide — Project 03 Resume Parser

---

## AWS Services for Resume Parsing

### 1. Ready-to-Use AI (No Model Needed)

| Service                    | What it does                                                                 | When to use                                        |
|----------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Amazon Textract**        | Extract text, tables, and key-value pairs from PDFs and images               | Replace your PyMuPDF + Tesseract pipeline          |
| **Amazon Comprehend**      | Named entity recognition for PERSON, ORG, DATE, LOCATION                    | Enhance entity extraction from extracted text      |
| **Amazon Bedrock**         | Claude/Titan to extract and structure resume fields via prompt               | When you need flexible, schema-free extraction     |

> **Amazon Textract** is the direct replacement for your PyMuPDF + spaCy pipeline. It handles PDF layout, tables, and forms out of the box with no model training required.

### 2. Host Your Own Model (Keep Current Stack)

| Service                    | What it does                                                        | When to use                                           |
|----------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **AWS App Runner**         | Run backend container — simplest, no VPC or cluster needed          | Quickest path to production                           |
| **Amazon ECS Fargate**     | Run backend + nlp-service containers in a private VPC               | Best match for your current microservice architecture |
| **Amazon ECR**             | Store your Docker images                                            | Used with App Runner, ECS, or EKS                     |

### 3. Train and Manage Your Model

| Service                         | What it does                                                        | When to use                                           |
|---------------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **Amazon Comprehend Custom**    | Train custom NER for resume-specific entities                       | When you need domain-specific entity extraction       |
| **AWS SageMaker**               | Train, track, register, and deploy your NER model                   | Full ML pipeline for custom entity extraction         |

### 4. Frontend Hosting

| Service               | What it does                                                                  |
|-----------------------|-------------------------------------------------------------------------------|
| **Amazon S3**         | Host your React build as a static website                                     |
| **Amazon CloudFront** | CDN in front of S3 — HTTPS, low latency globally                              |

### 5. Supporting Services

| Service                  | Purpose                                                                   |
|--------------------------|---------------------------------------------------------------------------|
| **Amazon S3**            | Store uploaded resume files and parsed JSON results                       |
| **AWS Secrets Manager**  | Store API keys and connection strings instead of .env files               |
| **Amazon CloudWatch**    | Track parsing latency, error rates, request volume                        |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  S3 + CloudFront — React Frontend                           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  AWS App Runner / ECS Fargate — Backend (FastAPI :8000)     │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────┐
│ ECS Fargate       │    │ Amazon Textract             │
│ NLP Service :8001 │    │ + Amazon Comprehend NER     │
│ spaCy + PyMuPDF   │    │ No model maintenance needed │
└───────────────────┘    └────────────────────────────┘
```

---

## Prerequisites

```bash
aws configure
AWS_REGION=eu-west-2
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
```

---

## Step 1 — Create ECR and Push Images

```bash
aws ecr create-repository --repository-name resumeparser/nlp-service --region $AWS_REGION
aws ecr create-repository --repository-name resumeparser/backend --region $AWS_REGION
ECR=$AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR
docker build -f docker/Dockerfile.nlp-service -t $ECR/resumeparser/nlp-service:latest ./nlp-service
docker push $ECR/resumeparser/nlp-service:latest
docker build -f docker/Dockerfile.backend -t $ECR/resumeparser/backend:latest ./backend
docker push $ECR/resumeparser/backend:latest
```

---

## Step 2 — Create S3 Bucket for Resume Files

```bash
aws s3 mb s3://resume-files-$AWS_ACCOUNT --region $AWS_REGION
aws s3api put-bucket-cors --bucket resume-files-$AWS_ACCOUNT --cors-configuration '{
  "CORSRules": [{"AllowedOrigins": ["*"], "AllowedMethods": ["GET","PUT","POST"], "AllowedHeaders": ["*"]}]
}'
```

---

## Step 3 — Deploy with App Runner

```bash
aws apprunner create-service \
  --service-name resumeparser-backend \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "'$ECR'/resumeparser/backend:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "NLP_SERVICE_URL": "http://nlp-service:8001"
        }
      }
    }
  }' \
  --instance-configuration '{"Cpu": "1 vCPU", "Memory": "2 GB"}' \
  --region $AWS_REGION
```

---

## Option B — Use Amazon Textract + Comprehend

```python
import boto3

textract = boto3.client("textract", region_name="eu-west-2")
comprehend = boto3.client("comprehend", region_name="eu-west-2")

def parse_resume(file_bytes: bytes) -> dict:
    # Extract text from PDF
    response = textract.detect_document_text(Document={"Bytes": file_bytes})
    text = " ".join([b["Text"] for b in response["Blocks"] if b["BlockType"] == "LINE"])

    # Extract entities
    entities = comprehend.detect_entities(Text=text[:5000], LanguageCode="en")
    result = {"raw_text": text, "entities": {}}
    for entity in entities["Entities"]:
        etype = entity["Type"]
        result["entities"].setdefault(etype, []).append(entity["Text"])
    return result
```

Add to requirements.txt: `boto3>=1.34.0`

---

## CI/CD — GitHub Actions

```yaml
name: Deploy to AWS
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: eu-west-2
      - uses: aws-actions/amazon-ecr-login@v2
      - run: |
          docker build -f docker/Dockerfile.backend \
            -t ${{ secrets.ECR_REGISTRY }}/resumeparser/backend:${{ github.sha }} ./backend
          docker push ${{ secrets.ECR_REGISTRY }}/resumeparser/backend:${{ github.sha }}
```

---

## Estimated Monthly Cost

| Service                    | Tier              | Est. Cost          |
|----------------------------|-------------------|--------------------|
| App Runner (backend)       | 1 vCPU / 2 GB     | ~$20–25/month      |
| App Runner (nlp-service)   | 1 vCPU / 2 GB     | ~$20–25/month      |
| ECR                        | Storage           | ~$1–2/month        |
| S3 + CloudFront            | Standard          | ~$1–5/month        |
| Amazon Textract            | Pay per page      | ~$1.50/1000 pages  |
| **Total (Option A)**       |                   | **~$42–57/month**  |
| **Total (Option B)**       |                   | **~$22–32/month**  |

For exact estimates → https://calculator.aws

---

## Teardown

```bash
aws ecr delete-repository --repository-name resumeparser/backend --force
aws ecr delete-repository --repository-name resumeparser/nlp-service --force
aws s3 rm s3://resume-files-$AWS_ACCOUNT --recursive
aws s3 rb s3://resume-files-$AWS_ACCOUNT
```
