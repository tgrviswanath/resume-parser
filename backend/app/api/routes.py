from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.service import parse_resume
import httpx

router = APIRouter(prefix="/api/v1", tags=["resume"])


@router.post("/parse")
async def parse(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return await parse_resume(content, file.filename)
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="NLP service unavailable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
