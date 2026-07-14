"""
routers/cases.py — Case (saved report) endpoints.
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from middleware.auth import get_current_user, AuthenticatedUser
import services.database as db

router = APIRouter()

VALID_STATUSES = {"draft", "in_review", "signed_off"}


def _token(r: Request) -> str:
    return r.headers.get("authorization", "").replace("Bearer ", "").replace("bearer ", "")


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
    status: str


@router.get("/cases")
async def list_all_cases(
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
):
    token = _token(request)
    clients = db.get_clients(user.user_id, token)
    all_cases = []
    for client in clients:
        cases = db.get_cases(client["id"], token)
        for case in cases:
            case["client_name"] = client.get("client_name", "")
        all_cases.extend(cases)
    all_cases.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"cases": all_cases, "total": len(all_cases)}


@router.get("/cases/{case_id}/compliance")
async def get_case_compliance(
    case_id: str,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
):
    token = _token(request)
    case = db.get_case(case_id, token)
    check_text = case.get("compliance_result", "") or ""
    items = []
    for i, line in enumerate(check_text.split("\n")):
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 2:
            status = ("PASS" if "| PASS" in line else
                      "FAIL" if "| FAIL" in line else
                      "FLAG" if "| FLAG" in line else "")
            if status:
                items.append({
                    "number": len(items) + 1,
                    "item": parts[0],
                    "status": status,
                    "finding": parts[2] if len(parts) > 2 else "",
                    "required_action": parts[3] if len(parts) > 3 else (
                        "No action required." if status == "PASS" else "Address before issue."
                    ),
                })
    passes = sum(1 for i in items if i["status"] == "PASS")
    flags  = sum(1 for i in items if i["status"] == "FLAG")
    fails  = sum(1 for i in items if i["status"] == "FAIL")
    total  = len(items)
    return {
        "case_id": case_id,
        "rag_rating": case.get("rag_rating", ""),
        "passes": passes, "flags": flags, "fails": fails,
        "total": total,
        "compliance_score": round((passes / total) * 100) if total > 0 else 0,
        "items": items,
        "critical_items": [i for i in items if i["status"] == "FAIL"],
        "flag_items":     [i for i in items if i["status"] == "FLAG"],
        "pass_items":     [i for i in items if i["status"] == "PASS"],
    }


@router.get("/cases/{case_id}")
async def get_case(
    case_id: str,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
):
    case = db.get_case(case_id, _token(request))
    raw = case.get("fact_find", "") or ""
    case["fact_find_structured"] = _parse_fact_find_sections(raw)
    return case


@router.delete("/cases/{case_id}")
async def delete_case(
    case_id: str,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
):
    db.delete_case(case_id, _token(request))
    return {"message": "Deleted", "case_id": case_id}


@router.patch("/cases/{case_id}/status")
async def update_status(
    case_id: str,
    request: Request,
    body: UpdateCaseStatusRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(400, f"Invalid status. Must be: {', '.join(VALID_STATUSES)}")
    db.update_case_status(case_id, body.status, _token(request))
    return {"message": "Status updated", "case_id": case_id, "status": body.status}


@router.get("/clients/{client_id}/cases")
async def list_client_cases(
    client_id: str,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
):
    cases = db.get_cases(client_id, _token(request))
    return {"cases": cases, "total": len(cases), "client_id": client_id}


@router.post("/clients/{client_id}/cases")
async def save_case(
    client_id: str,
    request: Request,
    body: SaveCaseRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    token = _token(request)
    version = db.get_next_version(client_id, token)
    case = db.save_case(
        user_id=user.user_id, client_id=client_id,
        case_title=body.case_title, fact_find=body.fact_find or "",
        part1=body.report_part1 or "", part2=body.report_part2 or "",
        part3=body.report_part3 or "", part4=body.report_part4 or "",
        compliance=body.compliance_result or "", rag_rating=body.rag_rating or "",
        passes=body.passes or 0, flags=body.flags or 0, fails=body.fails or 0,
        firm_name=body.firm_name or "", adviser_name=body.adviser_name or "",
        basis=body.basis or "", charges=body.charges or "",
        report_ref=body.report_ref or "", status=body.status or "draft",
        version=version, access_token=token,
    )
    if not case:
        raise HTTPException(500, "Could not save case.")
    return case


def _parse_fact_find_sections(raw: str) -> dict:
    if not raw:
        return {}
    MARKERS = ["PERSONAL","INCOME","EXPENDITURE","ASSETS","PENSION",
               "PROTECTION","LIABILITIES","OBJECTIVES","RISK","ESTATE","TAX"]
    sections, current, lines = {}, "general", []
    for line in raw.split("\n"):
        upper = line.upper().strip()
        matched = next((m for m in MARKERS if m in upper and len(line) < 60), None)
        if matched and "=" in line:
            if lines:
                sections[current] = _parse_fields(lines)
            current, lines = matched.lower(), []
        else:
            lines.append(line)
    if lines:
        sections[current] = _parse_fields(lines)
    return sections


def _parse_fields(lines: list) -> list:
    fields = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("="):
            continue
        if ":" in line:
            parts = line.split(":", 1)
            label, value = parts[0].strip(), parts[1].strip()
            if label and value:
                missing = "[MISSING" in value
                fields.append({
                    "field": label,
                    "value": value,
                    "confidence": 0.0 if missing else 0.9,
                    "source": "missing" if missing else "extracted",
                    "missing": missing,
                })
    return fields
