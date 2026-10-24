from typing import Any

from .groq_client import understand_conversation
from .scheme_matcher import load_schemes, match_schemes
from .settings import settings
from .storage import save_transcript, save_turn

SYSTEM_CONTEXT = "You are JanSathi. Keep responses short, friendly, and in the user's language. Never claim eligibility. Never invent government scheme facts."


class JanSathiAgent:
    def __init__(self, client=None) -> None:
        # `client` is accepted for compatibility with the earlier constructor.
        self.schemes = load_schemes(settings.schemes_file)
        self.history: list[dict[str, str]] = []
        self.profile: dict[str, Any] = {"state": None, "occupation": None, "age": None}
        self.language = settings.default_language
        self.turns = 0

    def respond(self, user_text: str) -> str:
        clean_text = user_text.strip()
        if not clean_text:
            return "I didn't catch that. Please say it again."

        self.turns += 1
        self.history.append({"role": "user", "content": clean_text})
        try:
            result = understand_conversation(
                [{"role": "system", "content": SYSTEM_CONTEXT}, *self.history]
            )
            extracted = result.get("profile", {})
            for key in ("state", "occupation", "age"):
                value = extracted.get(key)
                if value is not None:
                    self.profile[key] = value
            self.language = result.get("language") or self.language

            matches = match_schemes(self.profile, self.schemes)
            if matches:
                lines = []
                for scheme in matches[:3]:
                    status = "verified" if scheme.get("verified") else "NOT VERIFIED — illustrative demo data"
                    lines.append(f"• {scheme.get('name', 'Unnamed scheme')} [{status}]")
                    summary = scheme.get("summary")
                    if summary:
                        lines.append(f"  {summary}")
                    if scheme.get("official_url"):
                        lines.append(f"  Official link: {scheme['official_url']}")
                answer = result.get("response", "I found potentially relevant records.")
                answer += "\n\nPotentially relevant records (not an eligibility decision):\n" + "\n".join(lines)
            else:
                answer = result.get("response", "I can help narrow this down.")
                if self.profile.get("state") or self.profile.get("occupation"):
                    answer += "\nI couldn't find a matching record in the current demo database."

            save_transcript(clean_text, self.language)
            save_turn(clean_text, answer, self.language)
            self.history.append({"role": "assistant", "content": answer})
            if len(self.history) > 12:
                self.history = self.history[-12:]
            return answer
        except Exception as exc:
            # Print a useful local error without ever printing credentials.
            print(f"\n[JanSathi error] {type(exc).__name__}: {exc}")
            return "Sorry, I couldn't process that just now. Please check the terminal error and try again."
