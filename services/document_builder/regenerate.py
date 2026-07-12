"""
documents/regenerate.py — Rebuilds Word documents on demand from a
saved case record. This is the regenerate-on-demand approach: we store
only the text in the database, and rebuild the .docx instantly whenever
the user wants to download it. Output is identical every time.
"""
from services.document_builder.suitability_doc import build_suitability_doc
from services.document_builder.compliance_doc import build_compliance_doc

def suitability_from_case(case: dict, client_name: str):
    return build_suitability_doc(
        client_name,
        case.get("adviser_name", "") or "",
        case.get("firm_name", "") or "",
        case.get("basis", "") or "",
        case.get("charges", "") or "",
        case.get("report_ref", "") or "",
        case.get("report_part1", "") or "",
        case.get("report_part2", "") or "",
        case.get("report_part3", "") or "",
        case.get("report_part4", "") or "",
    )

def compliance_from_case(case: dict, client_name: str):
    return build_compliance_doc(
        client_name,
        case.get("adviser_name", "") or "",
        case.get("firm_name", "") or "",
        case.get("report_ref", "") or "",
        case.get("compliance_result", "") or "",
        case.get("passes", 0) or 0,
        case.get("flags", 0) or 0,
        case.get("fails", 0) or 0,
    )
