"""
core/pdf_reader.py — Extracts text from uploaded PDF files.

Handles:
  - Single PDF or multiple PDFs (merged for extraction)
  - Digital/typed PDFs (text layer present)
  - Tables within PDFs (pension statements, valuations)
  - Graceful failure for scanned/image-only PDFs

Does NOT handle:
  - Handwritten or scanned image PDFs (no OCR)
  - Password-protected PDFs
"""
import io
import pdfplumber


def extract_text_from_pdf(pdf_bytes: bytes) -> tuple[str, int, list[str]]:
    """
    Extracts all text from a PDF file.

    Returns:
        (full_text, page_count, warnings)
        full_text: concatenated text from all pages
        page_count: number of pages processed
        warnings: list of any issues found
    """
    warnings = []
    pages_text = []

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            page_count = len(pdf.pages)

            for i, page in enumerate(pdf.pages):
                page_text = ""

                # Extract regular text
                text = page.extract_text()
                if text:
                    page_text += text + "\n"

                # Extract tables (pension statements, valuations often use tables)
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row:
                            # Convert table row to readable text
                            row_text = "  |  ".join(
                                str(cell).strip() if cell else ""
                                for cell in row
                            )
                            if row_text.strip(" |"):
                                page_text += row_text + "\n"

                if page_text.strip():
                    pages_text.append(f"[Page {i+1}]\n{page_text.strip()}")
                else:
                    warnings.append(
                        f"Page {i+1} appears to be a scanned image — "
                        "text could not be extracted automatically."
                    )

        if not pages_text:
            warnings.append(
                "No text could be extracted from this PDF. "
                "It may be a scanned document. Please paste the text manually."
            )
            return "", page_count, warnings

        full_text = "\n\n".join(pages_text)
        return full_text, page_count, warnings

    except Exception as e:
        return "", 0, [f"Could not read PDF: {str(e)}"]


def extract_text_from_multiple_pdfs(pdf_files: list) -> tuple[str, dict]:
    """
    Extracts and merges text from multiple uploaded PDF files.

    Args:
        pdf_files: list of Streamlit UploadedFile objects

    Returns:
        (merged_text, summary)
        merged_text: all text from all PDFs combined with file headers
        summary: dict with per-file stats and warnings
    """
    all_text = []
    summary = {"files": [], "total_pages": 0, "warnings": []}

    for uploaded_file in pdf_files:
        pdf_bytes = uploaded_file.read()
        file_text, page_count, warnings = extract_text_from_pdf(pdf_bytes)

        file_info = {
            "name": uploaded_file.name,
            "pages": page_count,
            "extracted": bool(file_text.strip()),
            "warnings": warnings,
        }
        summary["files"].append(file_info)
        summary["total_pages"] += page_count
        summary["warnings"].extend(warnings)

        if file_text.strip():
            all_text.append(
                f"{'='*60}\n"
                f"SOURCE: {uploaded_file.name} ({page_count} pages)\n"
                f"{'='*60}\n"
                f"{file_text}"
            )

    merged = "\n\n".join(all_text)
    return merged, summary
