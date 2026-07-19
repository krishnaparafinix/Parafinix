"""
routers/clients.py — Client folder endpoints with extended profile.
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from middleware.auth import get_current_user, AuthenticatedUser
from services.supabase_client import get_anon_client, get_user_client
from config import settings
import services.database as db

router = APIRouter()


def _token(r: Request) -> str:
    return r.headers.get("authorization", "").replace("Bearer ", "").replace("bearer ", "")


def _db(token: str = None):
    if token:
        return get_user_client(token)
    return get_anon_client()


class CreateClientRequest(BaseModel):
    client_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    segment: Optional[str] = None
    portfolio_value: Optional[float] = None
    rag: Optional[str] = "GREEN"
    owner_id: Optional[str] = None


class UpdateClientRequest(BaseModel):
    client_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    segment: Optional[str] = None
    portfolio_value: Optional[float] = None
    rag: Optional[str] = None
    owner_id: Optional[str] = None


def _enrich(clients: list, token: str) -> list:
    cases_by_client = db.get_cases_for_clients([c["id"] for c in clients], token)
    enriched = []
    for c in clients:
        cases = cases_by_client.get(c["id"], [])
        c["case_count"] = len(cases)
        c["latest_rag"] = cases[0].get("rag_rating", "") if cases else ""
        c["latest_status"] = cases[0].get("status", "") if cases else ""
        enriched.append(c)
    return enriched


@router.get("")
async def list_clients(
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
):
    token = _token(request)
    clients = db.get_clients(user.user_id, token)
    return {"clients": _enrich(clients, token)}


@router.get("/stats")
async def get_dashboard_stats(
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Per-user dashboard counters (clients / reports / this month / pending review) in 2 queries flat."""
    return db.get_user_stats(user.user_id, _token(request))


@router.post("")
async def create_client(
    request: Request,
    body: CreateClientRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    token = _token(request)
    try:
        data = {
            "user_id": user.user_id,
            "client_name": body.client_name,
            "email": body.email,
            "phone": body.phone,
            "segment": body.segment,
            "portfolio_value": body.portfolio_value,
            "rag": body.rag or "GREEN",
            "owner_id": body.owner_id or user.user_id,
        }
        res = _db(token).table("clients").insert(data).execute()
        return res.data[0] if res.data else data
    except Exception as e:
        raise HTTPException(500, f"Could not create client: {e}")


@router.get("/{client_id}")
async def get_client(
    client_id: str,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
):
    token = _token(request)
    client = db.get_client_by_id(client_id, user.user_id, token)
    if not client:
        raise HTTPException(404, "Client not found.")
    cases = db.get_cases(client_id, token)
    client["case_count"] = len(cases)
    client["cases"] = cases
    return client


@router.patch("/{client_id}")
async def update_client(
    client_id: str,
    request: Request,
    body: UpdateClientRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    token = _token(request)
    data = {k: v for k, v in body.dict().items() if v is not None}
    if not data:
        raise HTTPException(400, "No fields to update.")
    try:
        res = _db(token).table("clients").update(data).eq("id", client_id).execute()
        return res.data[0] if res.data else {"message": "Updated", "client_id": client_id}
    except Exception as e:
        raise HTTPException(500, f"Could not update client: {e}")


@router.delete("/{client_id}")
async def delete_client(
    client_id: str,
    request: Request,
    user: AuthenticatedUser = Depends(get_current_user),
):
    db.delete_client_folder(client_id, _token(request))
    return {"message": "Deleted", "client_id": client_id}
