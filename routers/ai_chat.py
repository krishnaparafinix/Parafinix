from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from middleware.auth import get_current_user, AuthenticatedUser
from services.ai_client import call_drafting_model, call_compliance_model
from services.ai_prompts import COMPLIANCE_SYSTEM, COMPLIANCE_ITEMS
import services.database as db

router = APIRouter()

CHAT_SYSTEM = "You are a Senior Chartered Financial Planner and UK compliance expert with 25 years of experience. Answer in professional British English."

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = ""

class ComplianceRerunRequest(BaseModel):
    case_id: str

class ComplianceFixRequest(BaseModel):
    flag_item: str
    report_section: str
    client_context: Optional[str] = ""

def _token(r):
    return r.headers.get("authorization", "").replace("Bearer ", "").replace("bearer ", "")

@router.post("/chat")
async def ai_chat(body: ChatRequest, user: AuthenticatedUser = Depends(get_current_user)):
    msg = f"Context:\n{body.context[:2000]}\n\nQuestion: {body.message}" if body.context else body.message
    return {"reply": call_compliance_model(CHAT_SYSTEM, msg, max_tokens=1500)}

@router.post("/compliance/rerun")
async def compliance_rerun(request: Request, body: ComplianceRerunRequest, user: AuthenticatedUser = Depends(get_current_user)):
    token = _token(request)
    case = db.get_case(body.case_id, token)
    combined = "\n\n".join(filter(None, [case.get(f"report_part{i}", "") for i in range(1,5)]))
    if not combined.strip():
        raise HTTPException(400, "No report content found.")
    check_text = call_compliance_model(COMPLIANCE_SYSTEM, f"Report:\n{combined[:7000]}\n\n{COMPLIANCE_ITEMS}", max_tokens=2500)
    passes = sum(1 for l in check_text.split("\n") if "| PASS" in l)
    flags  = sum(1 for l in check_text.split("\n") if "| FLAG" in l)
    fails  = sum(1 for l in check_text.split("\n") if "| FAIL" in l)
    rag    = "RED" if fails > 2 else ("AMBER" if flags > 5 or fails > 0 else "GREEN")
    try:
        from supabase import create_client
        from config import settings
        c = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        c.auth.set_session(token, token)
        c.table("cases").update({"compliance_result": check_text, "passes": passes, "flags": flags, "fails": fails, "rag_rating": rag}).eq("id", body.case_id).execute()
    except Exception as e:
        raise HTTPException(500, f"DB update failed: {e}")
    return {"check_text": check_text, "passes": passes, "flags": flags, "fails": fails, "rag_rating": rag}

@router.post("/compliance/fix")
async def compliance_fix(body: ComplianceFixRequest, user: AuthenticatedUser = Depends(get_current_user)):
    prompt = f"Flag: {body.flag_item}\n\nSection:\n{body.report_section[:2000]}\n\nWrite a specific fix with a draft paragraph. British English."
    return {"flag": body.flag_item, "suggestion": call_drafting_model("You are a Senior UK Compliance Manager.", prompt, max_tokens=1000)}