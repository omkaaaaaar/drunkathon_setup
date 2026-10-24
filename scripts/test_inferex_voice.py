"""Smoke-test InferexAI STT/TTS from the JanSathi project root.

Usage:
  python scripts/test_inferex_voice.py --tts
  python scripts/test_inferex_voice.py --stt path/to/short-marathi-audio.wav
  python scripts/test_inferex_voice.py --both path/to/short-marathi-audio.wav
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jansathi.inferex_client import InferexClient  # noqa: E402
from jansathi.settings import settings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Test InferexAI STT/TTS.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tts", action="store_true", help="test text-to-speech")
    group.add_argument("--stt", metavar="AUDIO_FILE", help="transcribe an audio file")
    group.add_argument("--both", metavar="AUDIO_FILE", help="test STT then TTS")
    args = parser.parse_args()

    if settings.mock_mode:
        print("MOCK_MODE is still enabled. Set MOCK_MODE=false in .env and save it.")
        return 2

    client = InferexClient()
    if args.tts:
        text = "नमस्कार! मी जनसाथी आहे. सरकारी योजनांची माहिती शोधण्यात मी मदत करू शकतो."
        output = client.synthesize(text, ROOT / "jansathi_voice_test.mp3")
        print(f"TTS successful. Audio saved to: {output}")
        try:
            subprocess.run(["open", str(output)], check=False)
        except OSError:
            pass
        return 0

    audio_path = Path(args.stt if args.stt else args.both).expanduser()
    transcript = client.transcribe(audio_path, language="mr")
    print("\nTranscript:")
    print(transcript)

    if args.both:
        output = client.synthesize(
            f"तुम्ही असे सांगितले: {transcript}",
            ROOT / "jansathi_voice_test.mp3",
        )
        print(f"\nTTS successful. Audio saved to: {output}")
        try:
            subprocess.run(["open", str(output)], check=False)
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Voice test failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
