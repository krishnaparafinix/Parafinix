"""
core/preflight.py — Pre-flight check before report generation.

Performs a fast preliminary scan of the notes using the compliance
model (cheaper and faster than Opus) to identify:
  - What key data was found
  - What critical data is missing
  - What is present but unclear or ambiguous

Returns a structured summary the UI can display as a confirmation
screen before committing to a full two-pass report generation.
"""
from services.ai_client import call_compliance_model

PREFLIGHT_SYSTEM = """You are a Senior Paraplanner at a leading UK Independent Financial Advice firm.
You are reviewing meeting notes before drafting a premium-quality suitability report.
Your job is a quick data quality check — identify what is present, what is missing, and what is unclear.
Think like a professional who needs to produce a report suitable for presentation by a Chartered Financial Planner.
Output ONLY valid JSON. No explanation, no preamble, no markdown fences."""

PREFLIGHT_PROMPT = """Review these meeting notes and identify what data is present and what is missing.

MEETING NOTES:
{notes}

Return this exact JSON structure:

{{
  "client_name": "",
  "ready_to_generate": true,
  "confidence": "high",
  "found": [
    "list of key data items that ARE present in the notes"
  ],
  "missing_critical": [
    "list of CRITICAL items missing that will significantly impact report quality"
  ],
  "missing_minor": [
    "list of minor items missing that can be flagged as [MISSING] in the report"
  ],
  "unclear": [
    "list of items that are present but ambiguous or need clarification"
  ],
  "recommendation": "one sentence: proceed / add more detail / significant gaps"
}}

Rules:
- ready_to_generate: true if enough data exists for a useful report, false if critically incomplete
- confidence: "high" (good notes), "medium" (some gaps but workable), "low" (major gaps)
- found: list the main data categories found (income, pensions, objectives etc) - keep brief
- missing_critical: only truly critical items (e.g. no objectives stated, no income figures at all)
- missing_minor: things that would be nice to have but report can proceed without
- unclear: things mentioned but without enough detail to use confidently
- recommendation: honest one-sentence assessment

Return ONLY the JSON object."""


def run_preflight(notes: str) -> dict:
    """
    Runs a fast pre-flight check on the notes.
    Returns the parsed result dict, or a safe default on failure.
    """
    import json

    prompt = PREFLIGHT_PROMPT.format(notes=notes[:8000])  # cap input for speed

    raw = call_compliance_model(PREFLIGHT_SYSTEM, prompt, max_tokens=1000)

    # Strip any accidental markdown
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()

    try:
        result = json.loads(raw)
        # Ensure all expected keys exist
        result.setdefault("client_name", "")
        result.setdefault("ready_to_generate", True)
        result.setdefault("confidence", "medium")
        result.setdefault("found", [])
        result.setdefault("missing_critical", [])
        result.setdefault("missing_minor", [])
        result.setdefault("unclear", [])
        result.setdefault("recommendation", "Proceed with generation.")
        return result
    except Exception:
        # Safe fallback — let them proceed, don't block on a parse error
        return {
            "client_name": "",
            "ready_to_generate": True,
            "confidence": "medium",
            "found": ["Notes provided — proceeding with extraction"],
            "missing_critical": [],
            "missing_minor": [],
            "unclear": [],
            "recommendation": "Pre-flight check could not parse — proceeding with generation.",
            "_parse_error": True,
        }
