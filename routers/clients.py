"""
routers/clients.py — Client folder endpoints.

GET    /clients            → list user's client folders
POST   /clients            → create a client folder
DELETE /clients/{id}       → delete a client folder
"""
from fastapi import APIRouter, HTTPException
from middleware.auth import CurrentUser
from models.requests import CreateClientRequest

router = APIRouter()


@router.get("")
async def list_clients(user: CurrentUser):
    """Returns all client folders belonging to the authenticated user."""
    # Phase 3: return await database.get_clients(user.user_id)
    return {"clients": [], "user_id": user.user_id}


@router.post("")
async def create_client(body: CreateClientRequest, user: CurrentUser):
    """Creates a new client folder."""
    # Phase 3: return await database.create_client_folder(user.user_id, body.client_name)
    return {"message": "stub", "client_name": body.client_name}


@router.delete("/{client_id}")
async def delete_client(client_id: str, user: CurrentUser):
    """Deletes a client folder and all its saved cases."""
    # Phase 3: return await database.delete_client_folder(client_id)
    return {"message": "stub", "client_id": client_id}
