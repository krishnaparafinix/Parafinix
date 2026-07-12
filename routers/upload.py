"""
routers/upload.py — File upload endpoints.

POST   /upload/pdf  → extract text from PDF, return raw text
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from middleware.auth import CurrentUser
from services.pdf_reader import extract_text_from_pdf

router = APIRouter()


@router.post("/pdf")
async def upload_pdf(user: CurrentUser, file: UploadFile = File(...)):
    """
    Accepts a PDF file upload and extracts its text layer.
    Works for typed/digital PDFs. Scanned documents return a warning.
    The Lovable frontend passes the returned text to POST /generate/extract.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    pdf_bytes = await file.read()
    text, page_count, warnings = extract_text_from_pdf(pdf_bytes)

    return {
        "filename": file.filename,
        "page_count": page_count,
        "extracted_text": text,
        "word_count": len(text.split()) if text else 0,
        "warnings": warnings,
        "success": bool(text.strip()),
    }
