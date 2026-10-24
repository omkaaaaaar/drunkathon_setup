import json
from pathlib import Path
from typing import Any


def load_schemes(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def match_schemes(profile: dict[str, Any], schemes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return potentially relevant records; this is not an eligibility decision."""
    occupation = str(profile.get("occupation") or "").strip().lower()
    state = str(profile.get("state") or "").strip().lower()
    age = profile.get("age")
    try:
        age = int(age) if age is not None else None
    except (TypeError, ValueError):
        age = None

    matches: list[dict[str, Any]] = []
    for scheme in schemes:
        occupations = [str(x).strip().lower() for x in scheme.get("occupations", scheme.get("audiences", []))]
        states = [str(x).strip().lower() for x in scheme.get("states", [])]

        if occupation and occupations:
            if not any(occupation == item or occupation in item or item in occupation for item in occupations):
                continue
        if state and states:
            if not any(item in {"all", "all india", "india"} for item in states) and state not in states:
                continue
        minimum = scheme.get("min_age")
        maximum = scheme.get("max_age")
        if age is not None and minimum is not None and age < minimum:
            continue
        if age is not None and maximum is not None and age > maximum:
            continue
        matches.append(scheme)
    return matches
