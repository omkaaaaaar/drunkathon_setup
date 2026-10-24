import json
from pathlib import Path
from typing import Any


def load_schemes(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def match_schemes(profile: dict[str, Any], schemes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Conservative keyword matching for the MVP; this does not decide eligibility."""
    occupation = (profile.get("occupation") or "").strip().lower()
    state = (profile.get("state") or "").strip().lower()
    results = []
    for scheme in schemes:
        audiences = [item.lower() for item in scheme.get("audiences", [])]
        states = [item.lower() for item in scheme.get("states", [])]
        audience_match = not occupation or any(
            term in occupation or occupation in term for term in audiences
        )
        state_match = not state or "all" in states or state in states
        if audience_match and state_match:
            results.append(scheme)
    return results
