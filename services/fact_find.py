"""
core/fact_find.py — Fact-find extraction engine.

Takes raw meeting notes and extracts structured client data into
named fields across 10 categories. The AI fills what it can find,
leaves blanks where it cannot, and flags anything ambiguous.
"""
from services.ai_client import call_drafting_model

EXTRACTION_SYSTEM = """You are a senior UK paraplanner extracting structured data from raw meeting notes.

Your job is to read the notes carefully and extract every piece of client information into the exact JSON structure provided.

RULES:
1. Only use information explicitly stated in the notes
2. Leave the value as empty string "" if information is not in the notes
3. Write [UNCLEAR: reason] if information is present but ambiguous
4. Never invent or assume figures not in the notes
5. For lists (dependants, pensions, protection), return as many items as found
6. Return ONLY valid JSON. No preamble, no explanation, no markdown fences."""

EXTRACTION_PROMPT = """Extract all client information from these meeting notes into this exact JSON structure.
Fill every field you can find. Leave as "" if not found. Write [UNCLEAR: reason] if ambiguous.

MEETING NOTES:
{notes}

Return this JSON structure populated with the extracted data:
{{
  "personal": {{
    "client1_name": "",
    "client1_dob": "",
    "client2_name": "",
    "client2_dob": "",
    "address": "",
    "marital_status": "",
    "dependants": [
      {{"name": "", "age": "", "relationship": ""}}
    ],
    "client1_employment": "",
    "client1_employer": "",
    "client2_employment": "",
    "client2_employer": ""
  }},
  "income": {{
    "client1_gross_salary": "",
    "client1_net_monthly": "",
    "client2_gross_salary": "",
    "client2_net_monthly": "",
    "client1_bonus": "",
    "client2_bonus": "",
    "other_income": "",
    "salary_sacrifice": "",
    "monthly_surplus": ""
  }},
  "expenditure": {{
    "mortgage_payment": "",
    "total_monthly": "",
    "notes": ""
  }},
  "assets": {{
    "cash_savings": [
      {{"provider": "", "type": "", "value": ""}}
    ],
    "isas": [
      {{"provider": "", "type": "", "value": "", "contributions": ""}}
    ],
    "gia": [
      {{"provider": "", "value": ""}}
    ],
    "property_value": "",
    "mortgage_balance": "",
    "property_equity": "",
    "premium_bonds": ""
  }},
  "pensions": [
    {{
      "provider": "",
      "type": "",
      "current_value": "",
      "employee_contribution": "",
      "employer_contribution": "",
      "fund_name": "",
      "selected_retirement_age": "",
      "status": "",
      "notes": ""
    }}
  ],
  "protection": [
    {{
      "type": "",
      "provider": "",
      "benefit": "",
      "premium": "",
      "term": "",
      "basis": "",
      "notes": ""
    }}
  ],
  "liabilities": {{
    "mortgage_balance": "",
    "mortgage_rate": "",
    "mortgage_term": "",
    "mortgage_monthly": "",
    "other_loans": "",
    "credit_cards": "",
    "total_liabilities": ""
  }},
  "objectives": {{
    "primary_objective": "",
    "target_retirement_age_client1": "",
    "target_retirement_age_client2": "",
    "target_retirement_income": "",
    "secondary_objectives": "",
    "time_horizons": "",
    "priorities": "",
    "concerns": ""
  }},
  "risk": {{
    "questionnaire_score": "",
    "questionnaire_tool": "",
    "profile_assigned": "",
    "capacity_for_loss": "",
    "client_own_words": "",
    "investment_time_horizon": ""
  }},
  "estate_planning": {{
    "will_in_place": "",
    "will_date": "",
    "lpa_in_place": "",
    "iht_position": "",
    "beneficiaries_noted": "",
    "trust_arrangements": ""
  }},
  "tax": {{
    "client1_tax_band": "",
    "client2_tax_band": "",
    "cgt_position": "",
    "annual_allowance_used": "",
    "isa_allowance_used": "",
    "notes": ""
  }},
  "flags": [
    ""
  ]
}}

The "flags" array should list every item that is missing, unclear, or needs the paraplanner to confirm before generating a report.
Return ONLY the JSON object. No other text."""


def extract_fact_find(notes: str) -> dict:
    """
    Calls the AI to extract structured data from raw notes.
    Returns a dict with the extracted data, or None on failure.
    """
    import json
    prompt = EXTRACTION_PROMPT.format(notes=notes)
    raw = call_drafting_model(EXTRACTION_SYSTEM, prompt, max_tokens=4000)
    # Strip any accidental markdown fences
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()
    try:
        return json.loads(raw)
    except Exception:
        return None


def fact_find_to_notes(data: dict) -> str:
    """
    Converts the structured (possibly edited) fact-find dict back into
    clean, well-organised meeting notes for the report generator.
    This is what gets passed to the report drafting engine.
    """
    lines = []

    def section(title):
        lines.append(f"\n{'='*50}")
        lines.append(f"{title.upper()}")
        lines.append('='*50)

    def field(label, value):
        if value and value != "" and not (isinstance(value, list) and len(value) == 0):
            lines.append(f"{label}: {value}")

    p = data.get("personal", {})
    section("Client Personal Details")
    field("Client 1", p.get("client1_name"))
    field("Date of Birth", p.get("client1_dob"))
    field("Client 2", p.get("client2_name"))
    field("Date of Birth (2)", p.get("client2_dob"))
    field("Address", p.get("address"))
    field("Marital Status", p.get("marital_status"))
    for d in p.get("dependants", []):
        if d.get("name"):
            lines.append(f"Dependant: {d.get('name')}, Age {d.get('age')}, {d.get('relationship')}")
    field("Client 1 Employment", p.get("client1_employment"))
    field("Client 1 Employer", p.get("client1_employer"))
    field("Client 2 Employment", p.get("client2_employment"))
    field("Client 2 Employer", p.get("client2_employer"))

    inc = data.get("income", {})
    section("Income")
    field("Client 1 Gross Salary", inc.get("client1_gross_salary"))
    field("Client 1 Net Monthly", inc.get("client1_net_monthly"))
    field("Client 2 Gross Salary", inc.get("client2_gross_salary"))
    field("Client 2 Net Monthly", inc.get("client2_net_monthly"))
    field("Client 1 Bonus", inc.get("client1_bonus"))
    field("Other Income", inc.get("other_income"))
    field("Salary Sacrifice", inc.get("salary_sacrifice"))
    field("Monthly Surplus", inc.get("monthly_surplus"))

    exp = data.get("expenditure", {})
    section("Expenditure")
    field("Mortgage/Rent Payment", exp.get("mortgage_payment"))
    field("Total Monthly Expenditure", exp.get("total_monthly"))
    field("Notes", exp.get("notes"))

    assets = data.get("assets", {})
    section("Assets & Savings")
    field("Property Value", assets.get("property_value"))
    field("Mortgage Balance", assets.get("mortgage_balance"))
    field("Property Equity", assets.get("property_equity"))
    field("Premium Bonds", assets.get("premium_bonds"))
    for acc in assets.get("cash_savings", []):
        if acc.get("value"):
            lines.append(f"Cash Savings: {acc.get('provider','Unknown')} — {acc.get('type','')} — {acc.get('value')}")
    for isa in assets.get("isas", []):
        if isa.get("value"):
            lines.append(f"ISA: {isa.get('provider','Unknown')} — {isa.get('type','')} — Value: {isa.get('value')} — Contributions: {isa.get('contributions','')}")
    for gia in assets.get("gia", []):
        if gia.get("value"):
            lines.append(f"GIA: {gia.get('provider','Unknown')} — Value: {gia.get('value')}")

    section("Pensions")
    for i, pen in enumerate(data.get("pensions", []), 1):
        if pen.get("provider") or pen.get("current_value"):
            lines.append(f"Pension {i}: {pen.get('provider','Unknown')} | {pen.get('type','')} | Value: {pen.get('current_value','')} | Employee: {pen.get('employee_contribution','')} | Employer: {pen.get('employer_contribution','')} | Fund: {pen.get('fund_name','')} | Target age: {pen.get('selected_retirement_age','')} | Status: {pen.get('status','')} | {pen.get('notes','')}")

    section("Protection")
    for pol in data.get("protection", []):
        if pol.get("type") or pol.get("benefit"):
            lines.append(f"Policy: {pol.get('type','')} | Provider: {pol.get('provider','')} | Benefit: {pol.get('benefit','')} | Premium: {pol.get('premium','')} | Term: {pol.get('term','')} | Basis: {pol.get('basis','')} | {pol.get('notes','')}")

    liab = data.get("liabilities", {})
    section("Liabilities")
    field("Mortgage Balance", liab.get("mortgage_balance"))
    field("Mortgage Rate", liab.get("mortgage_rate"))
    field("Mortgage Term", liab.get("mortgage_term"))
    field("Mortgage Monthly", liab.get("mortgage_monthly"))
    field("Other Loans", liab.get("other_loans"))
    field("Credit Cards", liab.get("credit_cards"))

    obj = data.get("objectives", {})
    section("Objectives")
    field("Primary Objective", obj.get("primary_objective"))
    field("Target Retirement Age (Client 1)", obj.get("target_retirement_age_client1"))
    field("Target Retirement Age (Client 2)", obj.get("target_retirement_age_client2"))
    field("Target Retirement Income", obj.get("target_retirement_income"))
    field("Secondary Objectives", obj.get("secondary_objectives"))
    field("Time Horizons", obj.get("time_horizons"))
    field("Priorities", obj.get("priorities"))
    field("Concerns", obj.get("concerns"))

    risk = data.get("risk", {})
    section("Attitude to Risk & Capacity for Loss")
    field("Questionnaire Tool", risk.get("questionnaire_tool"))
    field("Score", risk.get("questionnaire_score"))
    field("Profile Assigned", risk.get("profile_assigned"))
    field("Capacity for Loss", risk.get("capacity_for_loss"))
    field("Client Own Words", risk.get("client_own_words"))
    field("Investment Time Horizon", risk.get("investment_time_horizon"))

    ep = data.get("estate_planning", {})
    section("Estate Planning")
    field("Will in Place", ep.get("will_in_place"))
    field("Will Date", ep.get("will_date"))
    field("LPA in Place", ep.get("lpa_in_place"))
    field("IHT Position", ep.get("iht_position"))
    field("Beneficiaries Noted", ep.get("beneficiaries_noted"))
    field("Trust Arrangements", ep.get("trust_arrangements"))

    tax = data.get("tax", {})
    section("Tax Position")
    field("Client 1 Tax Band", tax.get("client1_tax_band"))
    field("Client 2 Tax Band", tax.get("client2_tax_band"))
    field("CGT Position", tax.get("cgt_position"))
    field("Annual Allowance Used", tax.get("annual_allowance_used"))
    field("ISA Allowance Used", tax.get("isa_allowance_used"))
    field("Notes", tax.get("notes"))

    return "\n".join(lines)
