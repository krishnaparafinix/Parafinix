"""
routers/cases.py — Case (saved report) endpoints.

GET    /cases                       → all cases for the user (across all clients)
GET    /cases/{id}                  → single case
DELETE /cases/{id}                  → delete a case
PATCH  /cases/{id}/status           → update workflow status
GET    /clients/{id}/cases          → cases for a specific client
POST   /clients/{id}/cases          → save a new case
"""
from fastapi import APIRouter, HTTPException, Request
from middleware.auth import CurrentUser
from models.requests import SaveCaseRequest, UpdateCaseStatusRequest
import services.database as db

router = APIRouter()

VALID_STATUSES = {"draft", "in_review", "signed_off"}


def _token(request: Request) -> str:
    return request.headers.get("authorization", "").replace("Bearer ", "").replace("bearer ", "")


@router.get("/cases")
async def list_all_cases(user: CurrentUser, request: Request):
    """All cases across all clients for the logged-in user."""
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


@router.get("/cases/{case_id}")
async def get_case(case_id: str, user: CurrentUser, request: Request):
    return db.get_case(case_id, _token(request))


@router.delete("/cases/{case_id}")
async def delete_case(case_id: str, user: CurrentUser, request: Request):
    db.delete_case(case_id, _token(request))
    return {"message": "Deleted", "case_id": case_id}


@router.patch("/cases/{case_id}/status")
async def update_status(
    case_id: str, body: UpdateCaseStatusRequest, user: CurrentUser, request: Request
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}",
        )
    db.update_case_status(case_id, body.status, _token(request))
    return {"message": "Status updated", "case_id": case_id, "status": body.status}


@router.get("/clients/{client_id}/cases")
async def list_client_cases(client_id: str, user: CurrentUser, request: Request):
    cases = db.get_cases(client_id, _token(request))
    return {"cases": cases, "total": len(cases), "client_id": client_id}


@router.post("/clients/{client_id}/cases")
async def save_case(
    client_id: str, body: SaveCaseRequest, user: CurrentUser, request: Request
):
    token = _token(request)
    version = db.get_next_version(client_id, token)
    case = db.save_case(
        user_id=user.user_id,
        client_id=client_id,
        case_title=body.case_title,
        fact_find=body.fact_find or "",
        part1=body.report_part1 or "",
        part2=body.report_part2 or "",
        part3=body.report_part3 or "",
        part4=body.report_part4 or "",
        compliance=body.compliance_result or "",
        rag_rating=body.rag_rating or "",
        passes=body.passes or 0,
        flags=body.flags or 0,
        fails=body.fails or 0,
        firm_name=body.firm_name or "",
        adviser_name=body.adviser_name or "",
        basis=body.basis or "",
        charges=body.charges or "",
        report_ref=body.report_ref or "",
        status=body.status or "draft",
        version=version,
        access_token=token,
    )
    if not case:
        raise HTTPException(status_code=500, detail="Could not save case.")
    return case


@router.get("/cases/{case_id}/compliance")
async def get_case_compliance(case_id: str, user: CurrentUser, request: Request):
    """
    Returns structured compliance data for a case.
    Parses the stored compliance_result text into structured items
    with status, finding and required action for each of the 28 checks.
    """
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
            status = "PASS" if "| PASS" in line else ("FAIL" if "| FAIL" in line else "FLAG" if "| FLAG" in line else "")
            if status:
                items.append({
                    "number": i + 1,
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
    score  = round((passes / total) * 100) if total > 0 else 0

    return {
        "case_id": case_id,
        "rag_rating": case.get("rag_rating", ""),
        "passes": passes,
        "flags": flags,
        "fails": fails,
        "total": total,
        "compliance_score": score,
        "items": items,
        "critical_items": [i for i in items if i["status"] == "FAIL"],
        "flag_items": [i for i in items if i["status"] == "FLAG"],
        "pass_items": [i for i in items if i["status"] == "PASS"],
    }
