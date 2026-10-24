"""Multilingual-friendly matching for JanSathi scheme records."""
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

ALIASES = {
    "शेतकरी": "farmer", "शेती": "farmer", "किसान": "farmer", "किसानों": "farmer",
    "खेती": "farmer", "kisan": "farmer", "kisaan": "farmer", "shetkari": "farmer",
    "shetkar": "farmer", "farmer": "farmer", "farmers": "farmer", "agriculture": "farmer",
    "विद्यार्थी": "student", "विद्यार्थी": "student", "छात्र": "student", "छात्रा": "student",
    "student": "student", "students": "student",
    "महिला": "woman", "बाई": "woman", "स्त्री": "woman", "women": "woman", "woman": "woman",
    "मजूर": "worker", "कामगार": "worker", "मजदूर": "worker", "कामगारांसाठी": "worker",
    "worker": "worker", "labourer": "worker", "laborer": "worker",
    "ज्येष्ठ नागरिक": "senior citizen", "वृद्ध": "senior citizen", "senior citizen": "senior citizen",
    "pension": "pension", "पेन्शन": "pension", "निवृत्ती": "pension",
}
STATE_ALIASES = {
    "maharashtra": "maharashtra", "महाराष्ट्र": "maharashtra", "महाराष्ट्रात": "maharashtra",
    "mh": "maharashtra", "maharastra": "maharashtra",
    "india": "all india", "भारत": "all india", "bharat": "all india",
}

def normalize(text: Any) -> str:
    text = unicodedata.normalize("NFKC", str(text or "")).lower()
    text = text.replace("’", "'").replace("–", "-")
    text = re.sub(r"[^\w\s\u0900-\u097F\-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()

def load_schemes(path: Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)

def infer_profile_from_text(text: str) -> dict[str, Any]:
    """Lightweight fallback for common Marathi/Hindi/English/Romanized intents."""
    t = normalize(text)
    profile: dict[str, Any] = {}
    if any(k in t for k in [
        "farmer", "farmers", "agriculture", "kisan", "kisaan", "shetkari", "shetkar",
        "शेतकरी", "शेतकऱ", "शेती", "शेतकऱ्यांसाठी", "शेतात", "शेतमाल", "किसान", "खेती", "किसानों", "किसानी"
    ]):
        profile["occupation"] = "farmer"
    elif any(k in t for k in ["student", "vidyarthi", "छात्र", "छात्रा", "विद्यार्थी"]):
        profile["occupation"] = "student"
    elif any(k in t for k in ["woman", "women", "mahila", "महिला", "स्त्री", "बाई"]):
        profile["occupation"] = "woman"
    elif any(k in t for k in ["worker", "labourer", "laborer", "kamgar", "majdoor", "कामगार", "मजूर", "मजदूर"]):
        profile["occupation"] = "worker"
    elif any(k in t for k in ["senior citizen", "old age", "jyeshtha", "ज्येष्ठ नागरिक", "वृद्ध"]):
        profile["occupation"] = "senior citizen"
    if any(k in t for k in ["maharashtra", "maharastra", "mh", "महाराष्ट्र"]):
        profile["state"] = "maharashtra"
    age_match = re.search(r"\b(\d{1,3})\s*(?:years old|year old|yrs?|saal|sal|varsh|वर्ष|साल|वर्षांचा|वर्षांची)?\b", t)
    if age_match:
        age = int(age_match.group(1))
        if 0 <= age <= 120:
            profile["age"] = age
    return profile

def _canonical_occupation(value: Any) -> str:
    v = normalize(value)
    return ALIASES.get(v, v)

def match_schemes(profile: dict[str, Any], schemes: list[dict[str, Any]], query: str = "") -> list[dict[str, Any]]:
    """Rank likely relevant schemes; this is discovery, not an eligibility decision."""
    inferred = infer_profile_from_text(query)
    merged = dict(inferred)
    merged.update({k: v for k, v in (profile or {}).items() if v not in (None, "")})
    occupation = _canonical_occupation(merged.get("occupation"))
    state = STATE_ALIASES.get(normalize(merged.get("state")), normalize(merged.get("state")))
    try:
        age = int(merged["age"]) if merged.get("age") is not None else None
    except (TypeError, ValueError):
        age = None
    t = normalize(query)
    ranked = []
    for idx, scheme in enumerate(schemes):
        scheme_states = [STATE_ALIASES.get(normalize(x), normalize(x)) for x in scheme.get("states", [])]
        scheme_occ = [_canonical_occupation(x) for x in scheme.get("occupations", scheme.get("audiences", []))]
        if state and scheme_states and not any(x in {"all", "all india", "india"} for x in scheme_states):
            if state not in scheme_states:
                continue
        if occupation and scheme_occ:
            if not any(occupation == x or occupation in x or x in occupation for x in scheme_occ):
                # Do not discard broad central schemes if query asks a scheme by name.
                if not any(normalize(k) in t for k in scheme.get("keywords", []) + [scheme.get("name", "")]):
                    continue
        mn, mx = scheme.get("min_age"), scheme.get("max_age")
        if age is not None and ((mn is not None and age < mn) or (mx is not None and age > mx)):
            continue
        score = 0
        if occupation and any(occupation == x or occupation in x or x in occupation for x in scheme_occ):
            score += 4
        if state and state in scheme_states:
            score += 2
        terms = [scheme.get("name", "")] + scheme.get("keywords", [])
        score += sum(2 for k in terms if normalize(k) and normalize(k) in t)
        if any(x in t for x in ["yojana", "scheme", "योजना"]):
            score += 1
        ranked.append((score, idx, scheme))
    ranked.sort(key=lambda x: (-x[0], x[1]))
    return [x[2] for x in ranked]
