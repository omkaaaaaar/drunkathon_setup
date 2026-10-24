import json
from groq import Groq
from .settings import settings

SYSTEM_PROMPT = """You are JanSathi, a friendly multilingual assistant helping Indian citizens explore government schemes. Understand Marathi, Hindi, and English. Use all conversation turns to extract details already supplied. Never ask for Aadhaar numbers, OTPs, bank details, or biometrics. Do not invent schemes, benefits, deadlines, or official links. The application will check candidate schemes separately. Return ONLY valid JSON with exactly these keys: {\"intent\":\"discover_schemes|scheme_details|provide_information\",\"language\":\"mr|hi|en\",\"profile\":{\"state\":null,\"occupation\":null,\"age\":null},\"missing_fields\":[],\"response\":\"short natural response in the user's language\"}. Extract only details supported by the conversation. Use null for unknown details. Ask at most one concise follow-up question when useful."""


def _client() -> Groq:
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is missing from .env. Add a new Groq key locally; do not paste it into chat.")
    return Groq(api_key=settings.groq_api_key)


def understand_conversation(messages: list[dict[str, str]]) -> dict:
    response = _client().chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, *messages],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("Groq returned an empty response")
    result = json.loads(content)
    required = {"intent", "language", "profile", "missing_fields", "response"}
    if not required.issubset(result):
        raise ValueError("Groq response is missing required fields")
    if not isinstance(result["profile"], dict):
        raise ValueError("Groq returned an invalid profile")
    return result
