"""
documents/template_reader.py — Reads a firm's uploaded .docx template
and extracts its structure so the AI can follow the firm's own
headings and format rather than the default Parafinix layout.
"""
import mammoth

def extract_template_structure(template_file):
    """Returns (full_text, extracted_headings_summary)."""
    try:
        result = mammoth.extract_raw_text(template_file)
        text = result.value
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        headings = []
        for line in lines:
            if len(line) < 100 and (
                line[0].isdigit() or
                line.isupper() or
                any(line.startswith(p) for p in ['Section', 'SECTION', 'Part', 'PART', 'Chapter']) or
                len(line) < 60
            ):
                headings.append(line)
        structure = '\n'.join(headings[:80])
        return text, structure
    except Exception:
        return '', ''
