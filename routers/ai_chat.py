"""
routers/ai_chat.py — AI assistant and compliance endpoints.

POST /ai/chat              → data-aware assistant — returns {"reply": "..."}
                              Has tool-calling access to the user's own
                              clients, reports, and dashboard stats, plus
                              general product/compliance help.
POST /ai/compliance/rerun  → rerun 28-point check on a saved case
POST /ai/compliance/fix    → fix suggestion for a compliance flag
"""
import json
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from middleware.auth import get_current_user, require_admin, AuthenticatedUser
from services.ai_client import call_drafting_model, call_compliance_model, call_chat_agent
from services.ai_prompts import COMPLIANCE_SYSTEM, COMPLIANCE_ITEMS
import services.database as db

router = APIRouter()

CHAT_SYSTEM = """You are Parafinix AI's in-app assistant. You have two roles:

1. DATA ASSISTANT — you can answer questions about the user's own clients
   and reports using the tools available to you (get_clients,
   get_client_details, get_dashboard_stats). Always use a tool rather than
   guessing when the question is about specific client data, report
   status, RAG ratings, or account stats. Never invent client names,
   figures, or report content — if a tool returns no match, say so.

2. PRODUCT & COMPLIANCE HELP — you are also a Senior Chartered Financial
   Planner and UK compliance expert with 25 years of experience, able to
   help with FCA regulations, COBS 9A suitability requirements, pension
   rules, ISA and investment strategies, IHT planning, Consumer Duty
   obligations, and how to use the Parafinix app itself (fact-find
   extraction, report generation, the compliance review workflow).

Give clear, practical, professional answers in British English."""

CHAT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_clients",
            "description": "Get the list of all clients belonging to the current user, including report counts and last activity date.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_client_details",
            "description": "Get full details for a specific client by name, including all their saved reports, statuses, and RAG ratings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_name": {
                        "type": "string",
                        "description": "The client's name, or part of it — matched case-insensitively.",
                    },
                },
                "required": ["client_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_dashboard_stats",
            "description": "Get overall account stats: total clients, total reports, reports generated this month, reports pending review.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = ""


class ComplianceRerunRequest(BaseModel):
    case_id: str


class ComplianceFixRequest(BaseModel):
    flag_item: str
    report_section: str
    client_context: Optional[str] = ""


def _token(r: Request) -> str:
    return r.headers.get("authorization", "").replace("Bearer ", "").replace("bearer ", "")


def _execute_tool(tool_name: str, arguments: dict, user: AuthenticatedUser, token: str) -> dict:
    """Runs a tool call, scoped strictly to the current authenticated user."""
    if tool_name == "get_clients":
        clients = db.get_clients(user.user_id, token)
        return {"clients": [
            {
                "id": c["id"],
                "name": c.get("client_name"),
                "updated_at": c.get("updated_at"),
            }
            for c in clients
        ]}

    if tool_name == "get_client_details":
        name_query = (arguments.get("client_name") or "").lower()
        clients = db.get_clients(user.user_id, token)
        match = next(
            (c for c in clients if name_query in (c.get("client_name") or "").lower()),
            None,
        )
        if not match:
            return {"error": f"No client found matching '{arguments.get('client_name')}'"}
        cases = db.get_cases(match["id"], token)
        return {
            "client": {"id": match["id"], "name": match.get("client_name")},
            "reports": [
                {
                    "title": c.get("case_title"),
                    "status": c.get("status"),
                    "rag_rating": c.get("rag_rating"),
                    "version": c.get("version"),
                    "created_at": c.get("created_at"),
                }
                for c in cases
            ],
        }

    if tool_name == "get_dashboard_stats":
        return db.get_user_stats(user.user_id, token)

    return {"error": f"Unknown tool: {tool_name}"}


@router.post("/chat")
async def ai_chat(
    request: Request,
    body: ChatRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Data-aware AI assistant. Can answer questions about the logged-in
    user's own clients/reports (via tool-calling, scoped to their
    account only) as well as general product and compliance questions.
    """
    token = _token(request)

    messages = [
        {"role": "system", "content": CHAT_SYSTEM},
        {"role": "user", "content": body.message},
    ]

    message = call_chat_agent(messages, tools=CHAT_TOOLS)

    rounds = 0
    while message.tool_calls and rounds < 3:
        messages.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [tc.model_dump() for tc in message.tool_calls],
        })
        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments or "{}")
            result = _execute_tool(tool_call.function.name, args, user, token)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result),
            })
        message = call_chat_agent(messages, tools=CHAT_TOOLS)
        rounds += 1

    return {"reply": message.content or "I wasn't able to generate a response."}


@router.post("/compliance/rerun")
async def compliance_rerun(
    request: Request,
    body: ComplianceRerunRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Reruns the 28-point compliance check on a saved case."""
    token = _token(request)
    case = db.get_case(body.case_id, token)
    combined = "\n\n".join(filter(None, [
        case.get("report_part1", ""),
        case.get("report_part2", ""),
        case.get("report_part3", ""),
        case.get("report_part4", ""),
    ]))
    if not combined.strip():
        raise HTTPException(400, "No report content found in this case.")

    check_text = call_compliance_model(
        COMPLIANCE_SYSTEM,
        f"Report:\n{combined}\n\n{COMPLIANCE_ITEMS}",
        max_tokens=4000,
    )
    passes = sum(1 for l in check_text.split("\n") if "| PASS" in l)
    flags  = sum(1 for l in check_text.split("\n") if "| FLAG" in l)
    fails  = sum(1 for l in check_text.split("\n") if "| FAIL" in l)
    rag    = "RED" if fails > 2 else ("AMBER" if flags > 5 or fails > 0 else "GREEN")

    try:
        from services.supabase_client import get_user_client
        client = get_user_client(token)
        client.table("cases").update({
            "compliance_result": check_text,
            "passes": passes, "flags": flags, "fails": fails, "rag_rating": rag,
        }).eq("id", body.case_id).execute()
    except Exception as e:
        raise HTTPException(500, f"Database update failed: {e}")

    return {
        "check_text": check_text,
        "passes": passes, "flags": flags, "fails": fails,
        "rag_rating": rag, "message": "Compliance check updated.",
    }


@router.post("/compliance/fix")
async def compliance_fix(
    body: ComplianceFixRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Returns a specific fix suggestion for a compliance flag."""
    prompt = (
        f"Compliance flag: {body.flag_item}\n\n"
        f"Report section:\n{body.report_section[:2000]}\n\n"
        f"Client context: {body.client_context[:500]}\n\n"
        "Write a specific fix. Include: what text to add, which section, "
        "and a ready-to-use draft paragraph. Use professional British English."
    )
    suggestion = call_drafting_model(
        "You are a Senior UK Compliance Manager. Provide specific, actionable fixes for suitability report compliance gaps.",
        prompt, max_tokens=1000,
    )
    return {"flag": body.flag_item, "suggestion": suggestion}