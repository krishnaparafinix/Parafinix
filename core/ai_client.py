"""
core/ai_client.py — Single shared connection to the Mesh AI API.
Every other module calls through here. If we ever switch providers
or add a new model, this is the only file that changes.
"""
from openai import OpenAI
import streamlit as st
from config import MESH_API_KEY, MODEL_DRAFTING, MODEL_COMPLIANCE

@st.cache_resource
def get_ai_client() -> OpenAI:
    return OpenAI(base_url="https://api.meshapi.ai/v1", api_key=MESH_API_KEY)

def call_drafting_model(system_prompt: str, user_prompt: str, max_tokens: int = 6000) -> str:
    """Calls the high-quality drafting model (Claude Opus 4.8)."""
    client = get_ai_client()
    try:
        response = client.chat.completions.create(
            model=MODEL_DRAFTING,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"AI drafting failed: {e}")
        st.stop()

def call_compliance_model(system_prompt: str, user_prompt: str, max_tokens: int = 2500) -> str:
    """Calls the faster compliance-checking model (Claude Sonnet 4.6)."""
    client = get_ai_client()
    try:
        response = client.chat.completions.create(
            model=MODEL_COMPLIANCE,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Compliance check failed: {e}")
        st.stop()
