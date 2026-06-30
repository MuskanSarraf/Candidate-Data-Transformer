from typing import Any


def validate_projected(records: list[dict[str, Any]], config: dict[str, Any]) -> None:
    required_fields = [field for field in config.get("fields", []) if field.get("required")]
    for index, record in enumerate(records):
        for field in required_fields:
            value = _get_path(record, field["path"])
            if value in (None, "", []):
                raise ValueError(f"Record {index} is missing required field '{field['path']}'")
            expected_type = field.get("type")
            if expected_type and not _matches_type(value, expected_type):
                raise TypeError(f"Record {index} field '{field['path']}' expected {expected_type}")


def _matches_type(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "string[]":
        return isinstance(value, list) and all(isinstance(item, str) for item in value)
    if expected_type == "number":
        return isinstance(value, (int, float))
    if expected_type == "object":
        return isinstance(value, dict)
    return True


def _get_path(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
        if current is None:
            return None
    return current
