from typing import Any

from models.candidate import Candidate
from services.normalizer import normalize_phone, normalize_skill


def project_candidates(candidates: list[Candidate], config: dict[str, Any]) -> list[dict[str, Any]]:
    return [project_candidate(candidate, config) for candidate in candidates]


def project_candidate(candidate: Candidate, config: dict[str, Any]) -> dict[str, Any]:
    include_confidence = config.get("include_confidence", True)
    include_provenance = config.get("include_provenance", True)
    on_missing = config.get("on_missing", "null")

    output = {}
    fields = config.get("fields") or _default_fields()
    canonical = candidate.model_dump()

    for field in fields:
        target_path = field["path"]
        source_path = field.get("from", target_path)
        value = _get_path(canonical, source_path)
        value = _apply_projection_normalization(value, field.get("normalize"))

        if value is None:
            if field.get("required") and on_missing == "error":
                raise ValueError(f"Missing required field: {target_path}")
            if on_missing == "omit":
                continue
        _set_path(output, target_path, value)

    if include_confidence:
        output["overall_confidence"] = candidate.overall_confidence
    if include_provenance:
        output["provenance"] = [item.model_dump() for item in candidate.provenance]
    return output


def _default_fields() -> list[dict[str, str]]:
    return [
        {"path": "candidate_id"},
        {"path": "full_name"},
        {"path": "emails"},
        {"path": "phones", "normalize": "E164"},
        {"path": "location"},
        {"path": "links"},
        {"path": "headline"},
        {"path": "years_experience"},
        {"path": "skills"},
        {"path": "experience"},
        {"path": "education"},
    ]


def _get_path(data: Any, path: str) -> Any:
    current = data
    for part in _parse_path(path):
        if isinstance(part, int):
            if not isinstance(current, list) or part >= len(current):
                return None
            current = current[part]
        else:
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        if current is None:
            return None
    return current


def _set_path(data: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    current = data
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value


def _parse_path(path: str) -> list[str | int]:
    parts: list[str | int] = []
    for chunk in path.split("."):
        while "[" in chunk:
            prefix, rest = chunk.split("[", 1)
            if prefix:
                parts.append(prefix)
            index, chunk = rest.split("]", 1)
            parts.append(int(index))
            chunk = chunk.lstrip(".")
        if chunk:
            parts.append(chunk)
    return parts


def _apply_projection_normalization(value: Any, name: str | None) -> Any:
    if value is None or not name:
        return value
    if name == "E164":
        if isinstance(value, list):
            return [normalize_phone(item) for item in value if normalize_phone(item)]
        return normalize_phone(value)
    if name == "canonical":
        if isinstance(value, list):
            normalized = []
            for item in value:
                raw = item.get("name") if isinstance(item, dict) else item
                skill = normalize_skill(raw)
                if skill:
                    normalized.append(skill)
            return normalized
        return normalize_skill(value)
    return value
