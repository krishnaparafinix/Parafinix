"""
routers/upload.py — File upload endpoints.

POST   /upload/pdf   → accepts PDF upload, extracts text, returns raw text
                        Lovable then passes the text to /generate/extract
"""
from fastapi import APIRouter, UploadFile, File
from middleware.auth import CurrentUser

router = APIRouter()


@router.post("/pdf")
async def upload_pdf(user: CurrentUser, file: UploadFile = File(...)):
    """
    Accepts a PDF file upload.
    Extracts the text layer (works for typed/digital PDFs).
    Returns extracted text for the Lovable frontend to pass to /generate/extract.
    Scanned/image PDFs will return a warning and empty text.
    """
    # Phase 6: text, pages, warnings = extract_text_from_pdf(await file.read())
    return {
        "message": "stub",
        "filename": file.filename,
        "content_type": file.content_type,
    }
