"""
routers/cases.py — Case (saved report) endpoints.

GET    /clients/{client_id}/cases   → list cases for a client
POST   /clients/{client_id}/cases   → save a generated case
GET    /cases/{case_id}             → get a single case
DELETE /cases/{case_id}             → delete a case
PATCH  /cases/{case_id}/status      → update workflow status
"""
from fastapi import APIRouter
from middleware.auth import CurrentUser
from models.requests import SaveCaseRequest, UpdateCaseStatusRequest

router = APIRouter()


@router.get("/clients/{client_id}/cases")
async def list_cases(client_id: str, user: CurrentUser):
    """Returns all saved reports for a given client folder."""
    return {"cases": [], "client_id": client_id}


@router.post("/clients/{client_id}/cases")
async def save_case(client_id: str, body: SaveCaseRequest, user: CurrentUser):
    """Saves a generated report to a client folder."""
    return {"message": "stub", "client_id": client_id}


@router.get("/cases/{case_id}")
async def get_case(case_id: str, user: CurrentUser):
    """Returns a single saved case (used to regenerate document downloads)."""
    return {"message": "stub", "case_id": case_id}


@router.delete("/cases/{case_id}")
async def delete_case(case_id: str, user: CurrentUser):
    """Deletes a saved case permanently."""
    return {"message": "stub", "case_id": case_id}


@router.patch("/cases/{case_id}/status")
async def update_case_status(case_id: str, body: UpdateCaseStatusRequest, user: CurrentUser):
    """Moves a case through the workflow: draft → in_review → signed_off."""
    return {"message": "stub", "case_id": case_id, "new_status": body.status}
