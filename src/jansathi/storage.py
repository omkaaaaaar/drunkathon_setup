
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

def append_jsonl(filename: str, record: dict) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    path = DATA / filename

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **record,
    }

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def save_transcript(text: str, language: str) -> None:
    append_jsonl("transcripts.jsonl", {
        "text": text,
        "language": language,
    })

def save_turn(user_text: str, assistant_text: str, language: str) -> None:
    append_jsonl("conversations.jsonl", {
        "user": user_text,
        "assistant": assistant_text,
        "language": language,
    })

def load_schemes() -> list:
    path = DATA / "schemes.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)
