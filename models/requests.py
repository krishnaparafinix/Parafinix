"""
models/requests.py — Pydantic request body models.

Defines exactly what the Lovable frontend must send to each endpoint.
FastAPI validates automatically and returns 422 if fields are missing or wrong type.
"""
from pydantic import BaseModel
from typing import Optional


# ── CLIENTS ──────────────────────────────────────────────────
class CreateClientRequest(BaseModel):
    client_name: str


# ── CASES ────────────────────────────────────────────────────
class SaveCaseRequest(BaseModel):
    case_title: str
    fact_find: Optional[str] = ""
    report_part1: Optional[str] = ""
    report_part2: Optional[str] = ""
    report_part3: Optional[str] = ""
    report_part4: Optional[str] = ""
    compliance_result: Optional[str] = ""
    rag_rating: Optional[str] = ""
    passes: Optional[int] = 0
    flags: Optional[int] = 0
    fails: Optional[int] = 0
    firm_name: Optional[str] = ""
    adviser_name: Optional[str] = ""
    basis: Optional[str] = ""
    charges: Optional[str] = ""
    report_ref: Optional[str] = ""
    status: Optional[str] = "draft"
    version: Optional[int] = 1


class UpdateCaseStatusRequest(BaseModel):
    status: str  # draft | in_review | signed_off


# ── GENERATION ───────────────────────────────────────────────
class PreflightRequest(BaseModel):
    notes: str


class ExtractFactFindRequest(BaseModel):
    notes: str  # raw text (from paste or PDF extraction)


class GenerateReportRequest(BaseModel):
    client_name: str
    adviser_name: Optional[str] = ""
    firm_name: Optional[str] = ""
    basis: Optional[str] = "Independent"
    charges: Optional[str] = ""
    report_ref: Optional[str] = ""
    notes: str
    template_text: Optional[str] = ""  # firm's own template structure, if provided


# ── DOCUMENTS ────────────────────────────────────────────────
class BuildSuitabilityDocRequest(BaseModel):
    client_name: str
    adviser_name: Optional[str] = ""
    firm_name: Optional[str] = ""
    basis: Optional[str] = ""
    charges: Optional[str] = ""
    report_ref: Optional[str] = ""
    report_part1: str
    report_part2: Optional[str] = ""
    report_part3: Optional[str] = ""
    report_part4: Optional[str] = ""


class BuildComplianceDocRequest(BaseModel):
    client_name: str
    adviser_name: Optional[str] = ""
    firm_name: Optional[str] = ""
    report_ref: Optional[str] = ""
    check_text: str
    passes: int = 0
    flags: int = 0
    fails: int = 0


class BuildFactFindDocRequest(BaseModel):
    client_name: str
    adviser_name: Optional[str] = ""
    firm_name: Optional[str] = ""
    fact_find_data: dict          # the structured JSON from extract_fact_find()
    client_facing: bool = False   # True = client copy, False = internal copy
