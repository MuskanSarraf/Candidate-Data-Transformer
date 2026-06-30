import json
from pathlib import Path

from models.candidate import Provenance, SourceCandidate


def load_github_data(file_path: str) -> list[SourceCandidate]:
    """Load GitHub profile exports captured from a public API response."""
    path = Path(file_path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    rows = raw if isinstance(raw, list) else [raw] if isinstance(raw, dict) else []
    candidates = []
    for index, person in enumerate(rows):
        if not isinstance(person, dict):
            continue
        candidates.append(
            SourceCandidate(
                source="github",
                source_id=str(person.get("username") or person.get("login") or f"{path.name}:{index}"),
                source_confidence=0.7,
                data={
                    "full_name": person.get("name"),
                    "emails": [person.get("email")],
                    "headline": person.get("bio"),
                    "location": person.get("location"),
                    "github": person.get("github_url") or person.get("html_url"),
                    "skills": person.get("skills") or person.get("languages") or [],
                },
                provenance=[
                    Provenance(field="source_record", source="github", method="api_snapshot_adapter", confidence=0.7)
                ],
            )
        )
    return candidates
