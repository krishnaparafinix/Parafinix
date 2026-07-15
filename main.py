"""
main.py — Parafinix AI FastAPI backend.
Production-ready CORS, all routers registered.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers import clients, cases, generate, documents, upload, admin, auth, ai_chat

app = FastAPI(
    title="Parafinix AI API",
    description="Backend API for the Parafinix AI Paraplanner Co-Pilot.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────
# Explicit origins for production + regex for Lovable preview domains.
# FastAPI CORSMiddleware does not support wildcard subdomains in allow_origins
# so we use allow_origin_regex for all *.lovable.app patterns.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "https://lovable.app",
        "https://www.lovable.app",
    ],
    allow_origin_regex=(
        r"https://(.*\.lovable\.app"
        r"|.*\.lovableproject\.com"
        r"|.*\.railway\.app"
        r"|id-preview--.*\.lovable\.app)"
    ),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Type"],
    max_age=3600,
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


# ── STARTUP: pre-fetch JWKS ──────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """
    Warms up all connections at startup so the first real request
    is not penalised by cold-start latency.
    All steps are non-fatal — the app always starts even if warmup fails.
    """
    # 1. Pre-fetch Supabase JWKS (ES256 public keys for JWT verification)
    try:
        import middleware.auth as auth_mod
        auth_mod._jwks_cache = auth_mod._fetch_jwks()
        print(f"JWKS pre-loaded: {len(auth_mod._jwks_cache)} key(s) ✅")
    except Exception as e:
        print(f"JWKS pre-fetch skipped ({e})")

    # 2. Warm up Supabase connection pool
    try:
        from services.supabase_client import warmup
        warmup()
    except Exception as e:
        print(f"Supabase warmup skipped ({e})")

    print("Startup complete — Parafinix API ready")


# ── HEALTH ────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "parafinix-api", "version": "1.0.0"}


@app.get("/", tags=["Health"])
async def root():
    return {"message": "Parafinix AI API is running. See /docs for reference."}


@app.get("/debug", tags=["Health"])
async def debug():
    """Returns startup diagnostics — remove before production."""
    import sys, os
    results = {
        "python_version": sys.version,
        "env_vars_set": {
            "MESH_API_KEY": bool(os.environ.get("MESH_API_KEY")),
            "SUPABASE_URL": bool(os.environ.get("SUPABASE_URL")),
            "SUPABASE_ANON_KEY": bool(os.environ.get("SUPABASE_ANON_KEY")),
            "SUPABASE_JWT_SECRET": bool(os.environ.get("SUPABASE_JWT_SECRET")),
            "ADMIN_EMAIL": bool(os.environ.get("ADMIN_EMAIL")),
        },
        "imports": {}
    }
    for mod_name, import_str in [
        ("fastapi", "import fastapi"),
        ("pyjwt", "import jwt"),
        ("supabase", "import supabase"),
        ("openai", "import openai"),
        ("docx", "import docx"),
        ("pdfplumber", "import pdfplumber"),
        ("reportlab", "from reportlab.lib.pagesizes import A4"),
        ("httpx", "import httpx"),
        ("cryptography", "import cryptography"),
    ]:
        try:
            exec(import_str)
            results["imports"][mod_name] = "OK"
        except Exception as e:
            results["imports"][mod_name] = f"FAILED: {e}"
    return results
