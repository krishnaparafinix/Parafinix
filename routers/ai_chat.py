"""
routers/ai_chat.py — AI chat and compliance rerun endpoints.

POST   /ai/chat              → general AI assistant for paraplanning questions
POST   /ai/compliance/rerun  → rerun compliance check on an existing case
POST   /ai/compliance/fix    → generate a fix suggestion for a compliance flag
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from middleware.auth import CurrentUser
from services.ai_client import call_drafting_model, call_compliance_model
from services.ai_prompts import COMPLIANCE_SYSTEM, COMPLIANCE_ITEMS
import services.database as db

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = ""   # optional: paste report text or notes for context


class ComplianceRerunRequest(BaseModel):
    case_id: str


class ComplianceFixRequest(BaseModel):
    flag_item: str        # the specific compliance flag to fix
    report_section: str   # the relevant report section text
    client_context: str   # brief client context


CHAT_SYSTEM = """You are a Senior Chartered Financial Planner and compliance expert with 25 years of experience in UK financial advice. You assist paraplanners and financial advisers with technical questions about:
- FCA regulations and COBS requirements
- Suitability report writing and structure
- Pension rules and annual allowance
- ISA and investment strategies
- Inheritance Tax planning
- Consumer Duty obligations
- Best practice in financial planning

Give clear, practical, professional answers. Use British English. Always note when something requires professional judgement or regulatory confirmation. Never give specific regulated financial advice."""


@router.post("/chat")
async def ai_chat(body: ChatRequest, user: CurrentUser):
    """
    General AI assistant for paraplanning and compliance questions.
    The Lovable frontend can use this for an in-app help/chat feature.
    """
    user_msg = body.message
    if body.context:
        user_msg = f"Context from report/notes:\n{body.context[:2000]}\n\nQuestion: {body.message}"

    response = call_compliance_model(
        CHAT_SYSTEM,
        user_msg,
        max_tokens=1500,
    )
    return {"response": response}


@router.post("/compliance/rerun")
async def compliance_rerun(body: ComplianceRerunRequest, user: CurrentUser, request: Request):
    """
    Reruns the 28-point COBS 9A compliance check on an existing saved case.
    Updates the compliance_result, passes, flags, fails and rag_rating in the database.
    """
    token = request.headers.get("authorization", "").replace("Bearer ", "")
    case = db.get_case(body.case_id, token)

    # Combine all parts for compliance check
    combined = "\n\n".join(filter(None, [
        case.get("report_part1", ""),
        case.get("report_part2", ""),
        case.get("report_part3", ""),
        case.get("report_part4", ""),
    ]))

    if not combined.strip():
        raise HTTPException(status_code=400, detail="Case has no report content to check.")

    check_text = call_compliance_model(
        COMPLIANCE_SYSTEM,
        f"Report:\n{combined[:7000]}\n\n{COMPLIANCE_ITEMS}",
        max_tokens=2500,
    )

    passes = sum(1 for l in check_text.split("\n") if "| PASS" in l)
    flags  = sum(1 for l in check_text.split("\n") if "| FLAG" in l)
    fails  = sum(1 for l in check_text.split("\n") if "| FAIL" in l)
    rag    = "RED" if fails > 2 else ("AMBER" if flags > 5 or fails > 0 else "GREEN")

    # Update the case in the database
    try:
        from supabase import create_client
        from config import settings
        db_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        db_client.auth.set_session(token, token)
        db_client.table("cases").update({
            "compliance_result": check_text,
            "passes": passes,
            "flags": flags,
            "fails": fails,
            "rag_rating": rag,
        }).eq("id", body.case_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not update case: {e}")

    return {
        "check_text": check_text,
        "passes": passes,
        "flags": flags,
        "fails": fails,
        "rag_rating": rag,
        "message": "Compliance check completed and saved.",
    }


@router.post("/compliance/fix")
async def compliance_fix(body: ComplianceFixRequest, user: CurrentUser):
    """
    Generates a suggested fix for a specific compliance flag.
    Returns suggested text the paraplanner can copy into the report.
    """
    fix_prompt = f"""A UK suitability report has the following compliance flag:

FLAG: {body.flag_item}

RELEVANT REPORT SECTION:
{body.report_section[:2000]}

CLIENT CONTEXT:
{body.client_context[:500]}

Write a specific, professional suggestion to fix this compliance gap. Provide:
1. What text to add or change in the report
2. Which section it belongs in
3. A draft paragraph or table the paraplanner can use directly

Use professional British English. Be specific and actionable."""

    suggestion = call_drafting_model(
        "You are a Senior UK Compliance Manager reviewing suitability reports. Provide specific, actionable fixes for compliance gaps. Use professional British English.",
        fix_prompt,
        max_tokens=1000,
    )
    return {
        "flag": body.flag_item,
        "suggestion": suggestion,
    }
