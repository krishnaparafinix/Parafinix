"""
routers/ai_chat.py — AI assistant and compliance rerun endpoints.

POST /ai/chat              → paraplanning Q&A — returns {"reply": "..."}
POST /ai/compliance/rerun  → rerun 28-point check on a saved case
POST /ai/compliance/fix    → fix suggestion for a compliance flag
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from middleware.auth import CurrentUser
from services.ai_client import call_drafting_model, call_compliance_model
from services.ai_prompts import COMPLIANCE_SYSTEM, COMPLIANCE_ITEMS
import services.database as db

router = APIRouter()

CHAT_SYSTEM = """You are a Senior Chartered Financial Planner and UK compliance expert with 25 years of experience. You assist paraplanners and financial advisers with:
- FCA regulations and COBS 9A suitability requirements
- Report writing, structure and best practice
- Pension rules, annual allowance, lifetime allowance
- ISA, investment and tax planning
- Inheritance Tax and estate planning
- Consumer Duty obligations

Give clear, practical, professional answers in British English. Always note when professional judgement or regulatory confirmation is needed."""


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = ""


class ComplianceRerunRequest(BaseModel):
    case_id: str


class ComplianceFixRequest(BaseModel):
    flag_item: str
    report_section: str
    client_context: Optional[str] = ""


@router.post("/chat")
async def ai_chat(body: ChatRequest, user: CurrentUser):
    """
    General AI assistant for paraplanning questions.
    Returns {"reply": "..."} — matches frontend contract.
    """
    user_msg = body.message
    if body.context:
        user_msg = f"Context:\n{body.context[:2000]}\n\nQuestion: {body.message}"

    reply = call_compliance_model(CHAT_SYSTEM, user_msg, max_tokens=1500)
    return {"reply": reply}


@router.post("/compliance/rerun")
async def compliance_rerun(
    body: ComplianceRerunRequest, user: CurrentUser, request: Request
):
    """Reruns the 28-point compliance check on a saved case and updates the database."""
    token = request.headers.get("authorization", "").replace("Bearer ", "").replace("bearer ", "")
    case = db.get_case(body.case_id, token)

    combined = "\n\n".join(filter(None, [
        case.get("report_part1", ""),
        case.get("report_part2", ""),
        case.get("report_part3", ""),
        case.get("report_part4", ""),
    ]))

    if not combined.strip():
        raise HTTPException(status_code=400, detail="No report content found in this case.")

    check_text = call_compliance_model(
        COMPLIANCE_SYSTEM,
        f"Report:\n{combined[:7000]}\n\n{COMPLIANCE_ITEMS}",
        max_tokens=2500,
    )

    passes = sum(1 for l in check_text.split("\n") if "| PASS" in l)
    flags  = sum(1 for l in check_text.split("\n") if "| FLAG" in l)
    fails  = sum(1 for l in check_text.split("\n") if "| FAIL" in l)
    rag    = "RED" if fails > 2 else ("AMBER" if flags > 5 or fails > 0 else "GREEN")

    try:
        from supabase import create_client
        from config import settings
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        client.auth.set_session(token, token)
        client.table("cases").update({
            "compliance_result": check_text,
            "passes": passes,
            "flags": flags,
            "fails": fails,
            "rag_rating": rag,
        }).eq("id", body.case_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database update failed: {e}")

    return {
        "check_text": check_text,
        "passes": passes,
        "flags": flags,
        "fails": fails,
        "rag_rating": rag,
        "message": "Compliance check updated.",
    }


@router.post("/compliance/fix")
async def compliance_fix(body: ComplianceFixRequest, user: CurrentUser):
    """Returns a specific fix suggestion for a compliance flag."""
    prompt = (
        f"Compliance flag: {body.flag_item}\n\n"
        f"Report section:\n{body.report_section[:2000]}\n\n"
        f"Client context: {body.client_context[:500]}\n\n"
        "Write a specific fix for this compliance gap. Include:\n"
        "1. What text to add or change\n"
        "2. Which section it belongs in\n"
        "3. A ready-to-use draft paragraph\n\n"
        "Use professional British English."
    )
    suggestion = call_drafting_model(
        "You are a Senior UK Compliance Manager. Provide specific, actionable fixes for suitability report compliance gaps. Use professional British English.",
        prompt,
        max_tokens=1000,
    )
    return {"flag": body.flag_item, "suggestion": suggestion}
