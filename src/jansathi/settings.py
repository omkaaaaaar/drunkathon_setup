from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

@dataclass(frozen=True)
class Settings:
    mock_mode: bool = os.getenv("MOCK_MODE", "true").lower() in {"1", "true", "yes", "on"}
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

settings = Settings()
