import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.parser import parse_resume

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTS = {".pdf", ".docx", ".txt"}

router = APIRouter(prefix="/api/v1/nlp", tags=["resume-parser"])


def _validate_file(filename: str, content: bytes):
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Max {MAX_FILE_SIZE // (1024*1024)}MB")


@router.post("/parse")
async def parse(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    _validate_file(file.filename, content)
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, parse_resume, content, file.filename)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
