from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # MOCK_MODE controls Inferex voice features only; Groq is configured separately.
    mock_mode: bool = _as_bool(os.getenv("MOCK_MODE"), True)
    llm_provider: str = os.getenv("LLM_PROVIDER", "groq").strip().lower()
    groq_api_key: str = os.getenv("GROQ_API_KEY", "").strip()
    groq_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
    api_key: str = os.getenv("INFEREX_API_KEY", "").strip()
    base_url: str = os.getenv("INFEREX_BASE_URL", "https://api.inferexai.in/v1").rstrip("/")
    chat_model: str = os.getenv("INFEREX_CHAT_MODEL", "").strip()
    stt_model: str = os.getenv("INFEREX_STT_MODEL", "").strip()
    tts_model: str = os.getenv("INFEREX_TTS_MODEL", "").strip()
    tts_voice: str = os.getenv("INFEREX_TTS_VOICE", "").strip()
    stt_path: str = os.getenv("INFEREX_STT_PATH", "/audio/transcriptions")
    tts_path: str = os.getenv("INFEREX_TTS_PATH", "/audio/speech")
    timeout: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "45"))
    default_language: str = os.getenv("DEFAULT_LANGUAGE", "en").lower()
    schemes_file: Path = ROOT_DIR / os.getenv("SCHEMES_FILE", "data/schemes.json")
    transcripts_file: Path = ROOT_DIR / os.getenv("TRANSCRIPTS_FILE", "data/transcripts.jsonl")
    conversations_file: Path = ROOT_DIR / os.getenv("CONVERSATIONS_FILE", "data/conversations.jsonl")


settings = Settings()
