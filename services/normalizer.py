import hashlib
import re
from typing import Any

from models.candidate import Candidate, Experience, Links, Location, Provenance, Skill, SourceCandidate


SKILL_ALIASES = {
    "js": "JavaScript",
    "javascript": "JavaScript",
    "node": "Node.js",
    "nodejs": "Node.js",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "py": "Python",
    "python": "Python",
    "reactjs": "React",
    "springboot": "Spring Boot",
}

COUNTRY_ALIASES = {
    "india": "IN",
    "in": "IN",
    "nepal": "NP",
    "np": "NP",
    "united states": "US",
    "usa": "US",
    "us": "US",
}


def normalize_email(value: Any) -> str | None:
    if not value:
        return None
    email = str(value).strip().lower().strip(".,;:)")
    return email if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) else None


def normalize_phone(value: Any, default_country_code: str = "+91") -> str | None:
    if not value:
        return None
    text = str(value).strip()
    digits = re.sub(r"\D", "", text)
    if not digits:
        return None
    if text.startswith("+"):
        return f"+{digits}"
    if len(digits) == 10:
        return f"{default_country_code}{digits}"
    if len(digits) == 12 and digits.startswith("91"):
        return f"+{digits}"
    return f"+{digits}" if 8 <= len(digits) <= 15 else None


def normalize_country(value: Any) -> str | None:
    if not value:
        return None
    key = str(value).strip().lower()
    return COUNTRY_ALIASES.get(key, key.upper() if len(key) == 2 else None)


def normalize_skill(value: Any) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"\s+", " ", str(value).strip())
    key = cleaned.lower().replace(" ", "")
    return SKILL_ALIASES.get(key, cleaned.title() if cleaned.islower() else cleaned)


def normalize_date(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    match = re.search(r"(\d{4})(?:[-/](\d{1,2}))?", text)
    if not match:
        return None
    year = match.group(1)
    month = int(match.group(2) or 1)
    if not 1 <= month <= 12:
        return None
    return f"{year}-{month:02d}"


def stable_candidate_id(*parts: Any) -> str:
    seed = "|".join(str(part).lower().strip() for part in parts if part)
    if not seed:
        seed = "unknown"
    return "cand_" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]


def normalize_source_candidate(source_candidate: SourceCandidate) -> Candidate:
    data = source_candidate.data
    source = source_candidate.source
    confidence = source_candidate.source_confidence

    email_values = _as_list(data.get("emails") or data.get("email"))
    emails = _unique(filter(None, (normalize_email(email) for email in email_values)))

    phone_values = _as_list(data.get("phones") or data.get("phone"))
    phones = _unique(filter(None, (normalize_phone(phone) for phone in phone_values)))

    location = _normalize_location(data.get("location") or {})
    links = Links(
        github=data.get("github"),
        linkedin=data.get("linkedin"),
        portfolio=data.get("portfolio"),
        other=[link for link in _as_list(data.get("other_links")) if link],
    )

    skills = []
    for skill in _as_list(data.get("skills")):
        normalized = normalize_skill(skill)
        if normalized:
            skills.append(Skill(name=normalized, confidence=confidence, sources=[source]))

    experience = []
    for item in _as_list(data.get("experience")):
        if isinstance(item, dict):
            experience.append(
                Experience(
                    company=item.get("company"),
                    title=item.get("title"),
                    start=normalize_date(item.get("start")),
                    end=normalize_date(item.get("end")),
                    summary=item.get("summary"),
                )
            )

    name = _clean_string(data.get("full_name") or data.get("name"))
    candidate_id = data.get("candidate_id") or stable_candidate_id(emails[0] if emails else None, phones[0] if phones else None, name)

    fields_with_values = {
        "full_name": name,
        "emails": emails,
        "phones": phones,
        "location": location.model_dump(exclude_none=True),
        "links": links.model_dump(exclude_none=True),
        "headline": _clean_string(data.get("headline")),
        "years_experience": data.get("years_experience"),
        "skills": [skill.name for skill in skills],
        "experience": [item.model_dump(exclude_none=True) for item in experience],
    }
    provenance = [
        Provenance(field=field, source=source, method="normalize", confidence=confidence)
        for field, value in fields_with_values.items()
        if value not in (None, "", [], {})
    ]
    provenance.extend(source_candidate.provenance)

    return Candidate(
        candidate_id=candidate_id,
        full_name=name,
        emails=emails,
        phones=phones,
        location=location,
        links=links,
        headline=_clean_string(data.get("headline")),
        years_experience=_to_float(data.get("years_experience")),
        skills=skills,
        experience=experience,
        provenance=provenance,
        overall_confidence=confidence,
    )


def _normalize_location(value: Any) -> Location:
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",")]
        return Location(city=parts[0] if parts else None, country=normalize_country(parts[-1] if len(parts) > 1 else None))
    if not isinstance(value, dict):
        return Location()
    return Location(
        city=_clean_string(value.get("city")),
        region=_clean_string(value.get("region")),
        country=normalize_country(value.get("country") or value.get("country_code")),
    )


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _clean_string(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", str(value).strip())
    return cleaned or None


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _unique(values):
    seen = set()
    output = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output
