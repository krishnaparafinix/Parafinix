"""
routers/upload.py — File upload endpoints.

POST /upload/pdf
  - Accepts: multipart/form-data
  - Field name: file  (confirmed — matches frontend contract)
  - Returns:
    {
      "filename": "example.pdf",
      "page_count": 12,
      "extracted_text": "full text content...",
      "word_count": 3420,
      "warnings": [],
      "success": true
    }
  - extracted_text is passed directly to POST /generate/extract
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from middleware.auth import get_current_user, AuthenticatedUser
from services.pdf_reader import extract_text_from_pdf

router = APIRouter()


@router.post("/pdf")
async def upload_pdf(user: AuthenticatedUser = Depends(get_current_user), file: UploadFile = File(...)):
    """
    Extracts text from an uploaded PDF.

    Accepts: multipart/form-data, field name = file
    Works for: typed/digital PDFs (fact-finds, statements, reports)
    Does not work for: scanned/handwritten PDFs (no OCR)

    Returns extracted_text — pass this to POST /generate/extract
    to get the structured 60-field fact-find JSON.
    """
    if not file.content_type in ("application/pdf", "application/octet-stream"):
        if not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(400, "Only PDF files are accepted. "
                                     "Send as multipart/form-data with field name 'file'.")

    pdf_bytes = await file.read()

    if len(pdf_bytes) == 0:
        raise HTTPException(400, "Uploaded file is empty.")

    text, page_count, warnings = extract_text_from_pdf(pdf_bytes)

    return {
        "filename": file.filename,
        "page_count": page_count,
        "extracted_text": text,
        "word_count": len(text.split()) if text else 0,
        "warnings": warnings,
        "success": bool(text.strip()),
        "usage": "Pass extracted_text to POST /generate/extract to get structured fact-find data.",
    }
