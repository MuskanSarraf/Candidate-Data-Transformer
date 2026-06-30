import csv
from pathlib import Path

from models.candidate import Provenance, SourceCandidate


def load_recruiter_csv(file_path: str) -> list[SourceCandidate]:
    """Load a recruiter CSV export with already structured rows."""
    path = Path(file_path)
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError:
        return []

    candidates = []
    for index, row in enumerate(rows):
        if not any(row.values()):
            continue
        candidates.append(
            SourceCandidate(
                source="recruiter_csv",
                source_id=str(row.get("candidate_id") or f"{path.name}:{index}"),
                source_confidence=0.85,
                data={
                    "candidate_id": row.get("candidate_id"),
                    "full_name": row.get("name"),
                    "emails": [row.get("email")],
                    "phones": [row.get("phone")],
                    "headline": row.get("title"),
                    "location": {
                        "city": row.get("city"),
                        "region": row.get("region"),
                        "country": row.get("country"),
                    },
                    "skills": _split(row.get("skills")),
                    "years_experience": row.get("years_experience"),
                    "experience": [
                        {
                            "company": row.get("current_company"),
                            "title": row.get("title"),
                            "start": row.get("current_start"),
                        }
                    ],
                },
                provenance=[
                    Provenance(field="source_record", source="recruiter_csv", method="csv_adapter", confidence=0.85)
                ],
            )
        )
    return candidates


def _split(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.replace("|", ",").split(",") if part.strip()]
