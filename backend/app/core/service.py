import httpx
from app.core.config import settings

NLP_URL = settings.NLP_SERVICE_URL


async def parse_resume(file_bytes: bytes, filename: str) -> dict:
    """Forward uploaded file to nlp-service for parsing."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NLP_URL}/api/v1/nlp/parse",
            files={"file": (filename, file_bytes, _mime(filename))},
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()


def _mime(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
    }.get(ext, "application/octet-stream")
