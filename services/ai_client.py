"""
services/ai_client.py — Single shared connection to the Mesh AI API.

Extracted from core/ai_client.py in the Streamlit app.
Changes from Streamlit version:
  - Removed @st.cache_resource (not available in FastAPI)
  - Replaced st.error() / st.stop() with HTTPException
  - Client is created once at module level (equivalent to cache_resource)

Logic is identical to the Streamlit reference implementation.
"""
from openai import OpenAI
from fastapi import HTTPException, status
from config import settings

# Single client instance — created once at module import (equivalent to st.cache_resource)
_ai_client = OpenAI(
    base_url="https://api.meshapi.ai/v1",
    api_key=settings.MESH_API_KEY,
)

MODEL_DRAFTING    = "anthropic/claude-opus-4.8"
MODEL_COMPLIANCE  = "anthropic/claude-sonnet-4.6"


def call_drafting_model(system_prompt: str, user_prompt: str, max_tokens: int = 6000) -> str:
    """
    Calls the high-quality drafting model (Claude Opus 4.8 via Mesh).
    Used for all four passes of suitability report generation.
    """
    try:
        response = _ai_client.chat.completions.create(
            model=MODEL_DRAFTING,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI drafting model failed: {str(e)}",
        )


def call_compliance_model(system_prompt: str, user_prompt: str, max_tokens: int = 2500) -> str:
    """
    Calls the faster compliance-checking model (Claude Sonnet 4.6 via Mesh).
    Used for pre-flight checks and the 28-point COBS 9A compliance review.
    """
    try:
        response = _ai_client.chat.completions.create(
            model=MODEL_COMPLIANCE,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI compliance model failed: {str(e)}",
        )
