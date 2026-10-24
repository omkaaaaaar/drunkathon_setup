"""InferexAI client for JanSathi speech-to-text and text-to-speech."""
from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

import requests

from .settings import settings


class InferexClient:
    def __init__(self) -> None:
        self.api_key = settings.api_key
        self.base_url = settings.base_url.rstrip("/")
        self.timeout = settings.timeout
        self.mock_mode = settings.mock_mode
        self.last_detected_language: str | None = None
        self.last_stt_diagnostics: dict[str, Any] = {}

    @staticmethod
    def _language_code(language: str | None) -> str | None:
        """Normalize language names/codes. None or 'auto' means auto-detect."""
        if not language:
            return None
        normalized = language.strip().lower()
        if normalized in {"auto", "automatic", "detect", "none"}:
            return None
        aliases = {
            "mr": "mr-IN", "marathi": "mr-IN", "मराठी": "mr-IN", "mr-in": "mr-IN",
            "hi": "hi-IN", "hindi": "hi-IN", "हिंदी": "hi-IN", "hi-in": "hi-IN",
            "en": "en-IN", "english": "en-IN", "en-in": "en-IN",
        }
        return aliases.get(normalized, language.strip())

    @staticmethod
    def _raise_for_api_error(response: requests.Response) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            try:
                body = response.json()
                detail = body.get("error", {}).get("message") or body.get("message")
            except (ValueError, AttributeError):
                detail = response.text[:300]
            message = f"InferexAI returned HTTP {response.status_code}"
            if detail:
                message += f": {detail}"
            raise RuntimeError(message) from exc

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise RuntimeError("INFEREX_API_KEY is empty. Add it to your project .env file.")
        return {"Authorization": f"Bearer {self.api_key}"}

    def transcribe(self, audio_path: str | Path, language: str | None = None) -> str:
        """Transcribe audio. Omit language for automatic language detection."""
        path = Path(audio_path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Audio file not found: {path}")
        if self.mock_mode:
            raise RuntimeError("MOCK_MODE=true. Set MOCK_MODE=false to use real voice APIs.")
        if not settings.stt_model:
            raise RuntimeError("Set INFEREX_STT_MODEL in .env.")

        audio_size = path.stat().st_size
        if audio_size < 1000:
            raise RuntimeError(
                f"The recorded audio is only {audio_size} bytes. "
                "Please record for at least 2–3 seconds and try again."
            )

        self.last_detected_language = None
        language_code = self._language_code(language)
        data = {"model": settings.stt_model}
        if language_code:
            data["language_code"] = language_code

        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        with path.open("rb") as audio_file:
            response = requests.post(
                f"{self.base_url}{settings.stt_path}",
                headers=self._headers(),
                data=data,
                files={"file": (path.name, audio_file, content_type)},
                timeout=self.timeout,
            )
        self._raise_for_api_error(response)

        try:
            result = response.json()
        except ValueError as exc:
            self.last_stt_diagnostics = {
                "status_code": response.status_code,
                "content_type": response.headers.get("Content-Type"),
                "audio_bytes": audio_size,
                "language_hint": language_code or "auto",
            }
            raise RuntimeError(
                "InferexAI returned a non-JSON transcription response. "
                f"HTTP {response.status_code}; content type: "
                f"{response.headers.get('Content-Type', 'unknown')}; "
                f"uploaded audio: {audio_size} bytes."
            ) from exc

        if not isinstance(result, dict):
            raise RuntimeError(
                f"InferexAI returned an unexpected response type: {type(result).__name__}."
            )

        transcript = str(result.get("text") or "").strip()
        # Some APIs/models can provide segment text even if top-level text is empty.
        if not transcript and isinstance(result.get("segments"), list):
            transcript = " ".join(
                str(segment.get("text") or "").strip()
                for segment in result["segments"]
                if isinstance(segment, dict) and str(segment.get("text") or "").strip()
            ).strip()

        detected = result.get("language") or result.get("language_code")
        self.last_detected_language = str(detected) if detected else None
        self.last_stt_diagnostics = {
            "status_code": response.status_code,
            "content_type": response.headers.get("Content-Type"),
            "audio_bytes": audio_size,
            "audio_mime_type": content_type,
            "language_hint": language_code or "auto",
            "detected_language": self.last_detected_language or "not-returned",
            "duration": result.get("duration"),
            "response_keys": sorted(str(key) for key in result.keys()),
            "segment_count": len(result.get("segments", []))
            if isinstance(result.get("segments"), list) else 0,
            "transcript_chars": len(transcript),
        }

        if not transcript:
            # Do not log the full response or audio; just expose safe metadata for debugging.
            diagnostic = self.last_stt_diagnostics
            raise RuntimeError(
                "InferexAI returned no transcript text. "
                f"Diagnostics: HTTP {diagnostic['status_code']}, "
                f"audio={diagnostic['audio_bytes']} bytes, "
                f"mime={diagnostic['audio_mime_type']}, "
                f"language_hint={diagnostic['language_hint']}, "
                f"detected_language={diagnostic['detected_language']}, "
                f"duration={diagnostic['duration']}, "
                f"response_keys={diagnostic['response_keys']}, "
                f"segments={diagnostic['segment_count']}. "
                "Try a clear 3–6 second recording without background noise."
            )

        return transcript

    def synthesize(
        self,
        text: str,
        output_path: str | Path = "jansathi_reply.mp3",
        response_format: str = "mp3",
        voice: str | None = None,
    ) -> Path:
        """Synthesize speech and save the returned audio bytes."""
        if not text.strip():
            raise ValueError("Text to synthesize cannot be empty.")
        if self.mock_mode:
            raise RuntimeError("MOCK_MODE=true. Set MOCK_MODE=false to use real voice APIs.")
        if not settings.tts_model:
            raise RuntimeError("Set INFEREX_TTS_MODEL in .env.")

        selected_voice = (voice or settings.tts_voice or "").strip()
        if not selected_voice:
            raise RuntimeError("Set INFEREX_TTS_VOICE in .env.")
        supported_formats = {"mp3", "wav", "opus", "flac", "aac", "pcm", "mulaw"}
        if response_format not in supported_formats:
            raise ValueError(f"Unsupported response_format: {response_format}")

        destination = Path(output_path).expanduser()
        destination.parent.mkdir(parents=True, exist_ok=True)
        response = requests.post(
            f"{self.base_url}{settings.tts_path}",
            headers={**self._headers(), "Content-Type": "application/json"},
            json={
                "model": settings.tts_model,
                "input": text,
                "voice": selected_voice,
                "response_format": response_format,
            },
            timeout=self.timeout,
        )
        self._raise_for_api_error(response)
        if not response.content:
            raise RuntimeError("InferexAI TTS returned an empty audio response.")
        destination.write_bytes(response.content)
        return destination
