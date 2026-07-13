"""
routers/cases.py — Case (saved report) endpoints.

GET    /clients/{client_id}/cases   → list cases for a client
POST   /clients/{client_id}/cases   → save a generated case
GET    /cases/{case_id}             → get a single case
DELETE /cases/{case_id}             → delete a case
PATCH  /cases/{case_id}/status      → update workflow status
"""
from fastapi import APIRouter, HTTPException, Request
from middleware.auth import CurrentUser
from models.requests import SaveCaseRequest, UpdateCaseStatusRequest
import services.database as db

router = APIRouter()


@router.get("/clients/{client_id}/cases")
async def list_cases(client_id: str, user: CurrentUser, request: Request):
    """Returns all saved reports for a given client folder."""
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    cases = db.get_cases(client_id, token)
    return {"cases": cases}


@router.post("/clients/{client_id}/cases")
async def save_case(client_id: str, body: SaveCaseRequest, user: CurrentUser, request: Request):
    """Saves a generated report to a client folder."""
    token = request.headers.get("authorization", "").replace("Bearer ", "")
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


@router.get("/cases/{case_id}")
async def get_case(case_id: str, user: CurrentUser, request: Request):
    """Returns a single saved case (used to regenerate document downloads)."""
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    return db.get_case(case_id, token)


@router.delete("/cases/{case_id}")
async def delete_case(case_id: str, user: CurrentUser, request: Request):
    """Deletes a saved case permanently."""
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    db.delete_case(case_id, token)
    return {"message": "Deleted", "case_id": case_id}


@router.patch("/cases/{case_id}/status")
async def update_case_status(case_id: str, body: UpdateCaseStatusRequest,
                              user: CurrentUser, request: Request):
    """Moves a case through the workflow: draft → in_review → signed_off."""
    valid = {"draft", "in_review", "signed_off"}
    if body.status not in valid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid)}"
        )
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    db.update_case_status(case_id, body.status, token)
    return {"message": "Status updated", "case_id": case_id, "status": body.status}


@router.get("/cases")
async def list_all_cases(user: CurrentUser, request: Request):
    """Returns all saved cases across all clients for the logged-in user."""
    import services.database as db
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    # Get all clients first, then all their cases
    clients = db.get_clients(user.user_id, token)
    all_cases = []
    for client in clients:
        cases = db.get_cases(client["id"], token)
        for case in cases:
            case["client_name"] = client.get("client_name", "")
        all_cases.extend(cases)
    # Sort by created_at descending
    all_cases.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"cases": all_cases, "total": len(all_cases)}
