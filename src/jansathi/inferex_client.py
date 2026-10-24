"""Small InferexAI adapter. Keep API specifics configurable until verified by the API tester."""
import json
from pathlib import Path
from typing import Any
import requests
from .settings import settings


class InferexError(RuntimeError):
    pass


class InferexClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        if settings.api_key:
            self.session.headers.update({"Authorization": f"Bearer {settings.api_key}"})

    def _require_live_config(self, model: str, feature: str) -> None:
        if settings.mock_mode:
            return
        if not settings.api_key:
            raise InferexError("INFEREX_API_KEY is missing from .env")
        if not model:
            raise InferexError(f"Model ID for {feature} is missing from .env")

    def chat(self, messages: list[dict[str, str]]) -> str:
        if settings.mock_mode:
            last = messages[-1]["content"] if messages else ""
            if "PROFILE_JSON" in last:
                return json.dumps({"intent": "discover_schemes", "language": "en", "profile": {}, "next_question": "Which state do you live in?"})
            return "I can help you explore government schemes. To start, which state do you live in, and what best describes you: student, farmer, employed, self-employed, or something else?"
        self._require_live_config(settings.chat_model, "chat")
        response = self.session.post(
            f"{settings.base_url}/chat/completions",
            json={"model": settings.chat_model, "messages": messages, "temperature": 0.2},
            timeout=settings.timeout,
        )
        if not response.ok:
            raise InferexError(f"Chat API error {response.status_code}: {response.text[:500]}")
        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise InferexError(f"Unexpected chat response format: {data}") from exc

    def transcribe(self, audio_path: Path, language: str | None = None) -> str:
        self._require_live_config(settings.stt_model, "speech-to-text")
        if settings.mock_mode:
            raise InferexError("Mock mode doesn't transcribe audio. Type a message in the terminal, or configure live STT after confirming the API details.")
        url = settings.base_url.removesuffix("/v1") + settings.stt_path if settings.stt_path.startswith("/v1/") else settings.base_url + settings.stt_path
        with audio_path.open("rb") as audio_file:
            files = {"file": (audio_path.name, audio_file)}
            data: dict[str, str] = {"model": settings.stt_model}
            if language:
                data["language"] = language
            response = self.session.post(url, files=files, data=data, timeout=settings.timeout)
        if not response.ok:
            raise InferexError(f"STT API error {response.status_code}: {response.text[:500]}")
        result = response.json()
        text = result.get("text") or result.get("transcription")
        if not text:
            raise InferexError(f"Could not find transcription text in response: {result}")
        return text

    def synthesize(self, text: str, output_path: Path) -> Path:
        self._require_live_config(settings.tts_model, "text-to-speech")
        if settings.mock_mode:
            raise InferexError("Mock mode doesn't synthesize audio. Configure live TTS after confirming the API details.")
        url = settings.base_url.removesuffix("/v1") + settings.tts_path if settings.tts_path.startswith("/v1/") else settings.base_url + settings.tts_path
        payload: dict[str, Any] = {"model": settings.tts_model, "input": text}
        if settings.tts_voice:
            payload["voice"] = settings.tts_voice
        response = self.session.post(url, json=payload, timeout=settings.timeout)
        if not response.ok:
            raise InferexError(f"TTS API error {response.status_code}: {response.text[:500]}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)
        return output_path
