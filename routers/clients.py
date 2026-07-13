"""
routers/clients.py — Client folder endpoints.

GET    /clients              → list all client folders
POST   /clients              → create a client folder
GET    /clients/{id}         → get a single client with case count
DELETE /clients/{id}         → delete a client folder
"""
from fastapi import APIRouter, HTTPException, Request
from middleware.auth import CurrentUser
from models.requests import CreateClientRequest
import services.database as db

router = APIRouter()


def _token(request: Request) -> str:
    return request.headers.get("authorization", "").replace("Bearer ", "").replace("bearer ", "")


@router.get("")
async def list_clients(user: CurrentUser, request: Request):
    clients = db.get_clients(user.user_id, _token(request))
    # Add case_count to each client
    enriched = []
    for c in clients:
        cases = db.get_cases(c["id"], _token(request))
        c["case_count"] = len(cases)
        c["rag_rating"] = cases[0].get("rag_rating", "") if cases else ""
        c["latest_status"] = cases[0].get("status", "") if cases else ""
        enriched.append(c)
    return {"clients": enriched}


@router.post("")
async def create_client(body: CreateClientRequest, user: CurrentUser, request: Request):
    client = db.create_client_folder(user.user_id, body.client_name, _token(request))
    if not client:
        raise HTTPException(status_code=500, detail="Could not create client folder.")
    return client


@router.get("/{client_id}")
async def get_client(client_id: str, user: CurrentUser, request: Request):
    token = _token(request)
    clients = db.get_clients(user.user_id, token)
    client = next((c for c in clients if c["id"] == client_id), None)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")
    cases = db.get_cases(client_id, token)
    client["case_count"] = len(cases)
    client["cases"] = cases
    return client


@router.delete("/{client_id}")
async def delete_client(client_id: str, user: CurrentUser, request: Request):
    db.delete_client_folder(client_id, _token(request))
    return {"message": "Deleted", "client_id": client_id}
