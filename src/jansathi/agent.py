import json
from typing import Any
from .inferex_client import InferexClient
from .scheme_matcher import load_schemes, match_schemes
from .settings import settings

SYSTEM_PROMPT = """You are JanSathi, a kind voice-first assistant helping Indian citizens discover government schemes.
Use simple language and respond in the user's language: Marathi, Hindi, or English.
Ask only ONE follow-up question at a time. Collect only details relevant to scheme matching, such as state and occupation/student status; age range or income range only when relevant. Never request Aadhaar numbers, OTPs, bank details, or biometrics.
Never guarantee eligibility. Say 'potentially relevant' until official criteria have been verified. Do not invent scheme details, benefits, deadlines, or links. Be concise because answers will be spoken aloud."""

class JanSathiAgent:
    def __init__(self, client: InferexClient | None = None) -> None:
        self.client = client or InferexClient()
        self.schemes = load_schemes(settings.schemes_file)
        self.history: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.profile: dict[str, Any] = {}
        self.language = settings.default_language
        self.turns = 0

    def respond(self, user_text: str) -> str:
        clean_text = user_text.strip()
        if not clean_text:
            return "I didn't catch that. Please say it again."
        self.turns += 1
        self.history.append({"role": "user", "content": clean_text})
        schemes = match_schemes(self.profile, self.schemes)
        context = {
            "turn": self.turns,
            "known_profile": self.profile,
            "candidate_schemes": [
                {k: scheme.get(k) for k in ("name", "description", "audiences", "requires_verification", "official_url", "verified")}
                for scheme in schemes
            ],
            "instruction": "Understand the latest user turn. If key profile details are missing, ask one concise follow-up question. Otherwise explain potentially relevant schemes, why they may match, what must be verified, and the official link. Do not claim eligibility. Reply in the user's language."
        }
        # Add current structured context without relying on the LLM as the eligibility engine.
        self.history.append({"role": "system", "content": "CURRENT_CONTEXT_JSON: " + json.dumps(context, ensure_ascii=False)})
        answer = self.client.chat(self.history)
        # Keep history bounded for a lightweight local prototype.
        self.history.append({"role": "assistant", "content": answer})
        if len(self.history) > 13:
            self.history = [self.history[0]] + self.history[-12:]
        return answer
