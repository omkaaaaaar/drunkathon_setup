"""Local JanSathi multilingual voice landing page.

Run from the repository root:
    PYTHONPATH=src python web_app.py
"""
from __future__ import annotations

import os
import tempfile
import threading
import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request, session, url_for

from jansathi.agent import JanSathiAgent
from jansathi.inferex_client import InferexClient
from jansathi.settings import settings

ROOT = Path(__file__).resolve().parent
STATIC_GENERATED = ROOT / "static" / "generated"
STATIC_GENERATED.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.urandom(32)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

_agents: dict[str, JanSathiAgent] = {}
_agents_lock = threading.Lock()
ALLOWED_EXTENSIONS = {
    ".wav", ".mp3", ".m4a", ".mp4", ".webm", ".ogg", ".opus",
    ".flac", ".aac", ".aiff", ".amr", ".wma",
}

LANGUAGE_ALIASES = {
    "auto": "auto", "automatic": "auto", "": "auto",
    "mr": "mr-IN", "mr-in": "mr-IN", "marathi": "mr-IN", "मराठी": "mr-IN",
    "hi": "hi-IN", "hi-in": "hi-IN", "hindi": "hi-IN", "हिंदी": "hi-IN",
    "en": "en-IN", "en-in": "en-IN", "english": "en-IN",
}


def _normalize_ui_language(value: str | None) -> str:
    value = (value or "auto").strip()
    return LANGUAGE_ALIASES.get(value.lower(), "auto")


def _conversation_agent() -> JanSathiAgent:
    conversation_id = session.get("conversation_id")
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        session["conversation_id"] = conversation_id
    with _agents_lock:
        if conversation_id not in _agents:
            _agents[conversation_id] = JanSathiAgent()
        return _agents[conversation_id]


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({
        "ok": True,
        "mock_mode": settings.mock_mode,
        "stt_model_configured": bool(settings.stt_model),
        "tts_model_configured": bool(settings.tts_model),
        "llm_provider": os.getenv("LLM_PROVIDER", "groq"),
        "supported_ui_languages": ["auto", "mr-IN", "hi-IN", "en-IN"],
    })


@app.post("/api/voice")
def voice_turn():
    if settings.mock_mode:
        return jsonify({
            "error": "Voice APIs are in mock mode. Set MOCK_MODE=false in .env and restart the server."
        }), 503

    audio = request.files.get("audio")
    if audio is None or not audio.filename:
        return jsonify({"error": "No recording received. Tap the microphone and record again."}), 400

    suffix = Path(audio.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        mime = (audio.mimetype or "").lower()
        suffix = ".webm" if "webm" in mime else ".mp4" if "mp4" in mime else ".wav"

    selected_language = _normalize_ui_language(request.form.get("language"))
    # In Auto mode, deliberately omit language_code so Inferex can detect it.
    stt_language_hint = None if selected_language == "auto" else selected_language

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix="jansathi_upload_", suffix=suffix, delete=False) as temp:
            temp_path = Path(temp.name)
            audio.save(temp)

        inferex = InferexClient()
        transcript = inferex.transcribe(temp_path, language=stt_language_hint)
        if not transcript.strip():
            return jsonify({"error": "I couldn't hear clear speech. Please try again."}), 422

        detected_language = inferex.last_detected_language
        # If the user selected a language, honor that choice for the answer.
        # Otherwise use Inferex's detected language when available.
        reply_language = stt_language_hint or detected_language

        # Useful local diagnostic without logging audio or credentials.
        app.logger.info(
            "Voice turn completed: selected_language=%s detected_language=%s transcript_chars=%d",
            selected_language,
            detected_language or "not-returned",
            len(transcript),
        )

        agent = _conversation_agent()
        reply = agent.respond(transcript, language_hint=reply_language)
        if not reply or not reply.strip():
            return jsonify({"error": "JanSathi didn't produce a response. Please try again."}), 502

        audio_name = f"{uuid.uuid4().hex}.mp3"
        audio_path = STATIC_GENERATED / audio_name
        inferex.synthesize(reply, output_path=audio_path, response_format="mp3")
        return jsonify({
            "transcript": transcript,
            "reply": reply,
            "audio_url": url_for("static", filename=f"generated/{audio_name}"),
            "selected_language": selected_language,
            "detected_language": detected_language,
        })
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        app.logger.exception("Voice turn failed")
        return jsonify({"error": str(exc)}), 502
    finally:
        if temp_path:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass


@app.post("/api/reset")
def reset_conversation():
    conversation_id = session.get("conversation_id")
    if conversation_id:
        with _agents_lock:
            _agents.pop(conversation_id, None)
    session.pop("conversation_id", None)
    return jsonify({"ok": True})


@app.errorhandler(413)
def too_large(_error):
    return jsonify({"error": "That recording is too large. Please record a shorter question."}), 413


if __name__ == "__main__":
    if not settings.api_key:
        print("WARNING: INFEREX_API_KEY is empty in .env.")
    if settings.mock_mode:
        print("WARNING: MOCK_MODE=true. Set MOCK_MODE=false in .env.")
    print("\nJanSathi voice landing page: http://127.0.0.1:5000")
    print("Keep this Terminal open while testing. Press Ctrl+C to stop.\n")
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
