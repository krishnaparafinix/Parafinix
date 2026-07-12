"""
config.py — Central configuration for the Parafinix FastAPI backend.

Reads from environment variables (.env locally, Railway in production).
Raises a clear error on startup if any required variable is missing.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Mesh AI
    MESH_API_KEY: str

    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_JWT_SECRET: str

    # Application
    ADMIN_EMAIL: str = "admin.parafinix@gmail.com"
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
