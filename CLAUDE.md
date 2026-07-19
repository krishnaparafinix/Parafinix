# Parafinix AI — Project Context for Claude Code

This file gives Claude Code the full history and context of this project, built up over an extended planning session in Claude chat. Read this before making changes.

## Product Overview

Parafinix AI — "Your Report Wingman." B2B SaaS for UK independent financial advisers/paraplanners. Takes raw client meeting notes or uploaded PDFs, extracts structured data via AI, generates a Suitability Report + Compliance Review (COBS 9A). Solo founder: Krishna.

## Two Codebases (same GitHub repo, different branches)

| | Streamlit reference app | FastAPI production backend (this repo) |
|---|---|---|
| Branch | `main` | `parafinix-api` |
| Local path | `C:\Users\yadav\Parafinix` | `C:\Users\yadav\OneDrive\parafinix-api` (note: inside OneDrive, not directly in user folder) |
| Hosting | Streamlit Community Cloud, `parafinix.streamlit.app`, auto-rebuilds on push | Railway, `parafinix-api-production.up.railway.app`, **NO auto-deploy on trial plan — must manually trigger redeploy after every push** |

**Streamlit is the proving ground.** Features/prompts get tested there first, then ported to FastAPI. As of writing, FastAPI has drifted behind Streamlit in a few areas — see "Known gaps" below.

## Tech Stack

- AI: Mesh API (`api.meshapi.ai/v1`, OpenAI-SDK-compatible). Drafting model: `anthropic/claude-opus-4.8`. Compliance model: `anthropic/claude-sonnet-4.6`.
- Database/Auth: Supabase (`eu-west-2` London), project `oopbswfhihnvjvevesvo.supabase.co`
- Auth tokens are **ES256**, not HS256 — verified via JWKS at `.../auth/v1/.well-known/jwks.json`
- Admin bootstrap: registering with `admin.parafinix@gmail.com` auto-grants admin role (hardcoded, not scalable — flagged as tech debt)

## FastAPI Backend Structure (this repo)

```
routers/       auth, clients, cases, generate, documents, upload, admin, ai_chat
services/      supabase_client, database, ai_prompts, ai_client, word_builder,
               suitability_doc, compliance_doc, factfind_doc, regenerate,
               fact_find, pdf_reader, preflight
middleware/    ES256/JWKS auth verification
models/        Pydantic schemas
```

### Generation pipeline (3-pass, in `routers/generate.py`)
1. Pass 1 (8000 tokens) — Executive Summary + Sections 1–5
2. Pass 2 (8000 tokens) — Section 6, all recommendations in one pass
3. Pass 3 (6000 tokens) — Sections 7–11 + Paraplanner Check
4. Compliance — now a separate helper `_run_compliance_check()`, also exposed as its own `POST /generate/compliance` endpoint

### Known quirks / gotchas
- `POST /generate/extract`'s request field is `notes`, **not** `extracted_text`, despite what `upload.py`'s docstring says
- `POST /upload/pdf` only accepts genuine `.pdf` files — will reject `.doc`/`.docx` with a 400
- `POST /clients` requires `owner_id` to be a real UUID (the user's id), not a placeholder string

## Bugs Fixed So Far (don't reintroduce these)

1. **500 on all client/case endpoints** — `services/database.py` was missing `from services.supabase_client import get_anon_client, get_user_client`. Fixed.
2. **Compliance false-failing everything** — the compliance check only received `combined[:7000]` characters of the report (~1 section worth), so it never saw assets/pensions/recommendations that exist later in the doc, and falsely FAILed 15 items with a RED rating. Fixed by removing the truncation and bumping `max_tokens` from 2500 to 4000 in a new `_run_compliance_check()` helper, used by both `/generate/report` and the new standalone `/generate/compliance` endpoint.
3. **Broken mid-word "[PARAPLANNER CHECK]" table appearing after Section 5** — Pass 1's system-prompt-driven habit of always appending a paraplanner check collided with its own 8000-token limit, cutting the table off mid-word. Fixed by explicitly instructing Pass 1 not to include a paraplanner check (it's added properly in Pass 3).
4. **(Streamlit only, not yet ported here)** 4-pass generation was only running 2 of 4 passes due to a bug in `ui/page_generate.py` — FastAPI's 3-pass pipeline is architecturally different (combines what Streamlit split into 2 passes into 1), so it *may* still hit the same kind of truncation on complex clients with many recommendations. Not yet stress-tested against a 8-9-recommendation client the way Streamlit was. Watch for this if reports come back incomplete for complex clients.

## Known Gaps Between Streamlit and FastAPI (backlog, see Feature Ticket doc)

- FastAPI has **no persistent `fact_find_data`/`fact_find_notes` storage** on the client record — Streamlit does. Needed for a proper "Client Profile" experience.
- FastAPI has **no page-break-per-section formatting** in generated Word docs — Streamlit does (opt-in flag in `word_builder.py`'s `render_content()`).
- No rate limiting, no audit logging, no firm/team-level RLS (single-adviser-per-account model only).

## Frontend

A production React frontend is being built to consume this backend (previously attempted via Lovable, then Bolt.new — both hit credit limits during iteration; now building with Claude Code directly). See `Parafinix_Frontend_Spec.md` if present in the repo, or ask the user for it — it defines:
- Brand colours: navy `#0B1F3A`, blue `#3B82F6`, emerald `#10B981`. Inter font. Stripe/Linear/OpenAI-style minimal, no cheap gradients.
- Signature motif: an animated trace-line with a pulsing node, representing the report pipeline (Fact-Find → Extract → Generate → Review) — used in the logo and in generation progress indicators.
- Pages: Login, Dashboard, Client Profile (the core hub — details + generate buttons + report history), Fact-Find review screen.

## Working Style / Conventions

- UK spelling throughout report content (adviser not advisor, organised, etc.) — this is baked into the AI prompts, don't touch the prompt wording without reason.
- The person you're working with (Krishna) is a non-technical/semi-technical solo founder — prefer clear explanations over jargon, and confirm before large destructive changes (e.g. don't force-push, don't delete files without asking).
- Git commits should have clear, descriptive messages — this repo has a real history worth keeping readable.
- After any backend change, remind the user that **Railway does not auto-deploy** on the trial plan — they need to manually trigger a redeploy.
