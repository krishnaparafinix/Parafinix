"""
routers/clients.py — Client folder endpoints.

GET    /clients          → list user's client folders
POST   /clients          → create a client folder
DELETE /clients/{id}     → delete a client folder and all its cases
"""
from fastapi import APIRouter, HTTPException, Request
from middleware.auth import CurrentUser
from models.requests import CreateClientRequest
import services.database as db

router = APIRouter()


@router.get("")
async def list_clients(user: CurrentUser, request: Request):
    """Returns all client folders belonging to the authenticated user."""
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    clients = db.get_clients(user.user_id, token)
    return {"clients": clients}


@router.post("")
async def create_client(body: CreateClientRequest, user: CurrentUser, request: Request):
    """Creates a new client folder."""
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    client = db.create_client_folder(user.user_id, body.client_name, token)
    if not client:
        raise HTTPException(status_code=500, detail="Could not create client folder.")
    return client


@router.delete("/{client_id}")
async def delete_client(client_id: str, user: CurrentUser, request: Request):
    """Deletes a client folder and all its saved cases."""
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    db.delete_client_folder(client_id, token)
    return {"message": "Deleted", "client_id": client_id}


@router.get("/{client_id}")
async def get_client(client_id: str, user: CurrentUser, request: Request):
    """Returns a single client folder with its case count."""
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    clients = db.get_clients(user.user_id, token)
    client = next((c for c in clients if c["id"] == client_id), None)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")
    cases = db.get_cases(client_id, token)
    client["case_count"] = len(cases)
    client["recent_cases"] = cases[:3]  # last 3 for preview
    return client
