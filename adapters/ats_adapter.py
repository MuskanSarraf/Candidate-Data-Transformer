import json
from pathlib import Path

from models.candidate import Provenance, SourceCandidate


def load_ats_data(file_path: str) -> list[SourceCandidate]:
    """Load a semi-structured ATS JSON blob whose field names do not match ours."""
    path = Path(file_path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    rows = raw if isinstance(raw, list) else raw.get("candidates", []) if isinstance(raw, dict) else []
    candidates = []
    for index, person in enumerate(rows):
        if not isinstance(person, dict):
            continue
        candidates.append(
            SourceCandidate(
                source="ats_json",
                source_id=str(person.get("id") or f"{path.name}:{index}"),
                source_confidence=0.9,
                data={
                    "candidate_id": person.get("id"),
                    "full_name": person.get("candidateName") or person.get("name"),
                    "emails": [person.get("primaryEmail")],
                    "phones": [person.get("mobileNumber")],
                    "headline": person.get("jobTitle"),
                    "years_experience": person.get("yearsExperience"),
                    "location": {
                        "city": person.get("city"),
                        "country_code": person.get("countryCode"),
                    },
                    "skills": person.get("skills", []),
                    "experience": [
                        {
                            "company": person.get("currentCompany"),
                            "title": person.get("jobTitle"),
                            "start": person.get("currentStart"),
                            "end": None,
                        }
                    ]
                    if person.get("currentCompany") or person.get("jobTitle")
                    else [],
                },
                provenance=[
                    Provenance(field="source_record", source="ats_json", method="json_adapter", confidence=0.9)
                ],
            )
        )
    return candidates
