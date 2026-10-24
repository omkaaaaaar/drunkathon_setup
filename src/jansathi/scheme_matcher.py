
import json
from pathlib import Path
from typing import Any


def load_schemes(path: Path) -> list[dict[str, Any]]:
    """Load scheme records from the JSON database."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def match_schemes(
    profile: dict[str, Any],
    schemes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Find potentially relevant schemes.
    This is only a preliminary match, not an eligibility decision.
    """
    occupation = str(profile.get("occupation") or "").strip().lower()
    state = str(profile.get("state") or "").strip().lower()
    age = profile.get("age")

    matches = []

    for scheme in schemes:
        # Support the actual JSON schema: occupations.
        occupations = [
            str(item).strip().lower()
            for item in scheme.get(
                "occupations",
                scheme.get("audiences", []),
            )
        ]

        if occupation and occupations:
            if not any(
                occupation == item
                or occupation in item
                or item in occupation
                for item in occupations
            ):
                continue

        # "All India" schemes can match people in any state.
        states = [
            str(item).strip().lower()
            for item in scheme.get("states", [])
        ]

        if state and states:
            nationwide = any(
                item in {"all", "all india", "india", "nationwide"}
                for item in states
            )
            if not nationwide and state not in states:
                continue

        # Skip age-based exclusions only when age is known.
        if age is not None:
            try:
                numeric_age = int(age)
            except (TypeError, ValueError):
                numeric_age = None

            if numeric_age is not None:
                minimum = scheme.get("min_age")
                maximum = scheme.get("max_age")

                if minimum is not None and numeric_age < minimum:
                    continue

                if maximum is not None and numeric_age > maximum:
                    continue

        matches.append(scheme)

    return matches
