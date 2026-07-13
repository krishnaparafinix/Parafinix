"""
main.py — Parafinix AI FastAPI backend entry point.

Registers all routers, configures CORS for the Lovable React frontend,
and exposes a health check endpoint.

The Streamlit application remains the reference implementation and
continues to run independently at parafinix.streamlit.app.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import clients, cases, generate, documents, upload, admin, auth, ai_chat

app = FastAPI(
    title="Parafinix AI API",
    description="Backend API for the Parafinix AI Paraplanner Co-Pilot. "
                "Consumed by the Lovable React frontend.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────
# Allow the Lovable frontend (and localhost for development) to call the API.
# Tighten origins to the production Lovable domain once it is known.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://*.lovable.app",
        "https://*.lovableproject.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── ROUTERS ───────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/auth",      tags=["Authentication"])
app.include_router(clients.router,   prefix="/clients",   tags=["Clients"])
app.include_router(cases.router,     prefix="",           tags=["Cases"])
app.include_router(generate.router,  prefix="/generate",  tags=["Generation"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(upload.router,    prefix="/upload",    tags=["Upload"])
app.include_router(admin.router,     prefix="/admin",     tags=["Admin"])
app.include_router(ai_chat.router,   prefix="/ai",        tags=["AI Assistant"])


# ── HEALTH CHECK ──────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    """Railway and Lovable use this to confirm the API is running."""
    return {"status": "ok", "service": "parafinix-api", "version": "1.0.0"}


@app.get("/", tags=["Health"])
async def root():
    return {"message": "Parafinix AI API. See /docs for the full API reference."}
