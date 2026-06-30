import re
from pathlib import Path

from models.candidate import Provenance, SourceCandidate


def load_recruiter_notes(file_path: str) -> list[SourceCandidate]:
    """Extract lightweight candidate facts from free-text recruiter notes."""
    path = Path(file_path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []

    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    candidates = []
    for index, block in enumerate(blocks):
        email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", block)
        phone_match = re.search(r"(?:\+\d{1,3}[- ]?)?\d[\d -]{7,}\d", block)
        skills_match = re.search(r"skills?\s*[:=-]\s*([^\n.]+)", block, flags=re.IGNORECASE)
        years_match = re.search(r"(\d+(?:\.\d+)?)\+?\s+years?", block, flags=re.IGNORECASE)
        name_match = re.search(r"(?:candidate|name)\s*[:=-]\s*([A-Za-z .'-]+)", block, flags=re.IGNORECASE)
        headline_match = re.search(r"(?:headline|title)\s*[:=-]\s*([^\n.]+)", block, flags=re.IGNORECASE)
        if not (email_match or phone_match or name_match):
            continue

        candidates.append(
            SourceCandidate(
                source="recruiter_notes",
                source_id=f"{path.name}:{index}",
                source_confidence=0.6,
                data={
                    "full_name": name_match.group(1).strip() if name_match else None,
                    "emails": [email_match.group(0)] if email_match else [],
                    "phones": [phone_match.group(0)] if phone_match else [],
                    "headline": headline_match.group(1).strip() if headline_match else None,
                    "skills": _split_skills(skills_match.group(1)) if skills_match else [],
                    "years_experience": years_match.group(1) if years_match else None,
                },
                provenance=[
                    Provenance(field="source_record", source="recruiter_notes", method="regex_text_adapter", confidence=0.6)
                ],
            )
        )
    return candidates


def _split_skills(value: str) -> list[str]:
    return [part.strip() for part in re.split(r",|/|\|", value) if part.strip()]
