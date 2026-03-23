from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.parser import parse_resume

router = APIRouter(prefix="/api/v1/nlp", tags=["resume-parser"])


@router.post("/parse")
async def parse(file: UploadFile = File(...)):
    allowed = {".pdf", ".docx", ".txt"}
    ext = "." + file.filename.rsplit(".", 1)[-1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    try:
        content = await file.read()
        result = parse_resume(content, file.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
