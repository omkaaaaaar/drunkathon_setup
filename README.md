# JanSathi Voice AI

A lightweight, multilingual, voice-first assistant that helps people discover potentially relevant Government of India schemes through natural conversation in Marathi, Hindi, and English.

> Independent prototype. Not an official government service. Scheme data is illustrative until verified against official sources.

## MVP goals

- Have a short conversation to learn what the citizen is looking for.
- Ask only relevant follow-up questions.
- Match a small, curated scheme dataset against known profile details.
- Explain possible matches and provide official links when verified.
- Connect speech-to-text (STT), an LLM, and text-to-speech (TTS) through the InferexAI API.
- Keep the first interface in the terminal; no complex frontend.

## Quick start

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env  # Windows: copy .env.example .env
python -m jansathi
```

For the first run, set `MOCK_MODE=true`. This lets you test the conversation flow without API credits or credentials.

## InferexAI setup

1. Copy `.env.example` to `.env`.
2. Set `INFEREX_API_KEY` and the model IDs confirmed by your teammate.
3. Set `MOCK_MODE=false` only after the API tester confirms the correct endpoints, model IDs, request formats, and response formats.
4. Never commit `.env` or put API keys in frontend code.

The integration uses an OpenAI-compatible chat-completions request and configurable audio endpoints. Confirm the exact STT/TTS paths and model names against the account's current documentation before switching off mock mode.

## Project layout

```text
jansathi-voice-ai/
├── data/schemes.json       # small illustrative dataset; verify before real use
├── src/jansathi/
│   ├── __init__.py
│   ├── __main__.py
│   ├── agent.py            # conversational flow and follow-up questions
│   ├── inferex_client.py   # API adapter (mock mode supported)
│   ├── scheme_matcher.py   # deterministic matching, not LLM guessing
│   └── settings.py
├── .env.example
├── .gitignore
└── requirements.txt
```

## Conversation design

1. Identify the user's intent (find schemes, understand a scheme, or ask how to apply).
2. Collect relevant details gradually: state, age range, occupation/student status, and other details only if required by a scheme.
3. Match known details to scheme rules.
4. Explain why each scheme may be relevant, what still needs checking, and where the official information lives.
5. Never guarantee eligibility. Use official sources for current rules, amounts, and deadlines.

## Voice integration plan

- **STT:** capture a short recording, send it to the configured transcription endpoint, and use the returned text as the user's turn.
- **Agent:** maintain conversation state across turns; ask one follow-up at a time.
- **TTS:** speak the assistant's answer in the selected language.
- **Phone calls later:** keep audio input/output behind a small adapter so a telephony provider can replace the microphone without changing the agent logic.

## Safety and privacy

- Do not collect Aadhaar numbers, OTPs, bank details, or biometric data.
- Ask only for information needed to find relevant schemes.
- Clearly label unverified or illustrative scheme data.
- Do not send personal profile details to the LLM unless necessary.
