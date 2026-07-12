"""
models/responses.py — Pydantic response models.

Defines exactly what the API returns. Lovable reads these shapes.
"""
from pydantic import BaseModel
from typing import Optional, List


class ClientResponse(BaseModel):
    id: str
    client_name: str
    created_at: str
    updated_at: str


class CaseResponse(BaseModel):
    id: str
    client_id: str
    case_title: str
    status: str
    rag_rating: Optional[str] = ""
    passes: Optional[int] = 0
    flags: Optional[int] = 0
    fails: Optional[int] = 0
    version: Optional[int] = 1
    created_at: str


class PreflightResponse(BaseModel):
    client_name: str
    ready_to_generate: bool
    confidence: str           # high | medium | low
    found: List[str]
    missing_critical: List[str]
    missing_minor: List[str]
    unclear: List[str]
    recommendation: str


class ExtractFactFindResponse(BaseModel):
    data: dict                # the structured 60-field fact-find JSON
    flags: List[str]          # items that need paraplanner attention


class GenerateReportResponse(BaseModel):
    part1: str                # Executive Summary + Sections 1-5
    part2: str                # Recommendations first half
    part3: str                # Recommendations second half
    part4: str                # Sections 7-11 + Paraplanner Check
    check_text: str           # raw compliance check output
    passes: int
    flags: int
    fails: int
    rag_rating: str           # GREEN | AMBER | RED


class DocumentResponse(BaseModel):
    filename: str
    base64_content: str       # base64-encoded .docx — Lovable decodes + downloads
    mime_type: str = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
