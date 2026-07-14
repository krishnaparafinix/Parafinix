"""
routers/clients.py — Client folder endpoints with extended profile.
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from middleware.auth import get_current_user, AuthenticatedUser
from supabase import create_client
from config import settings
import services.database as db

router = APIRouter()


def _token(r: Request) -> str:
    return r.headers.get("authorization", "").replace("Bearer ", "").replace("bearer ", "")


def _db(token: str):
    c = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    try:
        c.auth.set_session(token, token)
    except Exception:
        pass
    return c


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
    enriched = []
    for c in clients:
        cases = db.get_cases(c["id"], token)
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
    clients = db.get_clients(user.user_id, token)
    client = next((c for c in clients if c["id"] == client_id), None)
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
