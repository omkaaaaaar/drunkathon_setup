"""Concise, conversational JanSathi agent with multilingual intent fallback."""
from typing import Any

from .groq_client import understand_conversation
from .scheme_matcher import load_schemes, match_schemes, infer_profile_from_text
from .settings import settings
from .storage import save_transcript, save_turn

LANGUAGE_NAMES = {
    "mr": "Marathi", "mr-in": "Marathi", "marathi": "Marathi", "मराठी": "Marathi",
    "hi": "Hindi", "hi-in": "Hindi", "hindi": "Hindi", "हिंदी": "Hindi",
    "en": "English", "en-in": "English", "english": "English",
}

def _language_name(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip().lower()
    return LANGUAGE_NAMES.get(value, value if value in {"Marathi", "Hindi", "English"} else None)

def _guess_language(text: str) -> str:
    # Script first. Romanized speech is ambiguous, so use common Marathi/Hindi markers.
    if any(ch in text for ch in "ळऴऱॅॉीूेैोौं"):
        return "Marathi"
    if any(ch in text for ch in "अआइईउऊऋएऐओऔकखगघचछजझटठडढणतथदधनपफबभमयरलवशषसह"):
        marathi = ["मला", "माझा", "माझी", "माझे", "आहे", "शेतकरी", "शेती", "पाहिजे", "कुठे", "काय", "योजना", "मिळेल"]
        return "Marathi" if any(x in text for x in marathi) else "Hindi"
    t = text.lower()
    if any(x in t for x in ["shetkari", "sheti", "mala pahije", "majha", "mazi", "ahe ka", "kuthli yojana"]):
        return "Marathi"
    if any(x in t for x in ["kisan", "mujhe", "chahiye", "kaise milega", "meri umar", "kaun si yojana"]):
        return "Hindi"
    return "English"

def _language_instruction(language: str) -> str:
    return (
        f"Reply only in {language}. Keep it conversational, warm and brief: 2–4 short sentences, "
        "normally under 65 words. Do not start with 'Sure!' or repeat the user's question. "
        "Do not output a long bullet list. Mention at most two relevant schemes by name, with "
        "one short benefit each. Ask just one useful follow-up question when needed. "
        "For Marathi, use natural Marathi in Devanagari; for Hindi, natural Hindi in Devanagari. "
        "Understand code-switching and romanized Marathi/Hindi; do not translate scheme names unnecessarily."
    )

SYSTEM_CONTEXT = """You are JanSathi, a friendly voice-first assistant for Indian government schemes.
Speak like a helpful local guide, not like a report. Keep answers short and conversational.
Use the provided scheme context; never invent benefit amounts, deadlines, age limits or official links.
Never guarantee eligibility or payment. If an age requirement is unknown, say it needs checking.
If the user says they live in Mumbai and are a farmer, clarify whether their farmland is in Maharashtra
and which district only if that detail is needed. Do not assume that their farm is in Mumbai.
When a likely scheme is found, explain it naturally instead of appending a database dump.
Do not mention internal database limitations if relevant records were found."""

class JanSathiAgent:
    def __init__(self, client=None) -> None:
        self.schemes = load_schemes(settings.schemes_file)
        self.history: list[dict[str, str]] = []
        self.profile: dict[str, Any] = {"state": None, "occupation": None, "age": None}
        self.language = settings.default_language
        self.turns = 0

    def respond(self, user_text: str, language_hint: str | None = None) -> str:
        clean_text = (user_text or "").strip()
        if not clean_text:
            return "I didn't catch that. कृपया पुन्हा सांगा / कृपया फिर से बोलें."

        self.turns += 1
        self.history.append({"role": "user", "content": clean_text})
        chosen_language = _language_name(language_hint) or _guess_language(clean_text)
        inferred = infer_profile_from_text(clean_text)
        self.profile.update({k: v for k, v in inferred.items() if v is not None})
        self.language = chosen_language

        try:
            # Give the model a small, relevant context rather than all 50 records.
            matches = match_schemes(self.profile, self.schemes, query=clean_text)
            verified_matches = [s for s in matches if s.get("verified") is True][:3]
            scheme_context = []
            for s in verified_matches:
                scheme_context.append({
                    "name": s.get("name"),
                    "summary": s.get("summary"),
                    "benefit": s.get("benefit"),
                    "age_requirement": s.get("age_requirement"),
                    "eligibility": s.get("eligibility"),
                    "official_url": s.get("official_url"),
                    "status_note": s.get("status_note"),
                })

            # The existing conversation extractor is retained, but it is asked to be concise.
            messages = [
                {"role": "system", "content": SYSTEM_CONTEXT + "\n\n" + _language_instruction(chosen_language)
                 + "\n\nRelevant official-source records (may be summarized; do not dump):\n"
                 + str(scheme_context)},
                *self.history,
            ]
            result = understand_conversation(messages) or {}
            extracted = result.get("profile", {}) or {}
            for key in ("state", "occupation", "age"):
                value = extracted.get(key)
                if value is not None:
                    self.profile[key] = value

            # Recalculate after model profile extraction.
            matches = match_schemes(self.profile, self.schemes, query=clean_text)
            verified_matches = [s for s in matches if s.get("verified") is True][:2]
            answer = str(result.get("response") or "").strip()

            if not answer:
                if verified_matches:
                    s = verified_matches[0]
                    if chosen_language == "Marathi":
                        answer = f"{s['name']} ही एक योजना तपासता येईल. पात्रता आणि वयोमर्यादा अधिकृत संकेतस्थळावर तपासावी. तुम्ही कोणत्या जिल्ह्यातील आहात?"
                    elif chosen_language == "Hindi":
                        answer = f"{s['name']} एक विकल्प हो सकता है। पात्रता और उम्र की शर्तें आधिकारिक वेबसाइट पर जाँचें। आप किस ज़िले से हैं?"
                    else:
                        answer = f"{s['name']} may be worth checking. Please confirm its age and eligibility rules on the official site. Which district is your farm in?"
                elif chosen_language == "Marathi":
                    answer = "मी मदत करतो. तुम्हाला शेतकरी, शिक्षण, आरोग्य की पेन्शन यापैकी कोणत्या प्रकारची योजना हवी आहे?"
                elif chosen_language == "Hindi":
                    answer = "मैं मदद करता हूँ। आपको किसान, पढ़ाई, स्वास्थ्य या पेंशन में से किस तरह की योजना चाहिए?"
                else:
                    answer = "I can help. Are you looking for farmer, education, health or pension support?"

            # Hard cap noisy LLM answers, then use a concise deterministic response if it rambles.
            plain = answer.strip()
            if len(plain) > 520 or plain.count("\n") >= 3 or "Potentially relevant verified records" in plain:
                if verified_matches:
                    s = verified_matches[0]
                    if chosen_language == "Marathi":
                        plain = f"{s['name']} तपासता येईल. पात्रता आणि वयोमर्यादा अधिकृत संकेतस्थळावर तपासा. तुमची शेती कोणत्या जिल्ह्यात आहे?"
                    elif chosen_language == "Hindi":
                        plain = f"{s['name']} देखी जा सकती है। पात्रता और उम्र की शर्तें आधिकारिक वेबसाइट पर जाँचें। आपका खेत किस ज़िले में है?"
                    else:
                        plain = f"{s['name']} may be worth checking. Confirm the age and eligibility rules on its official site. Which district is your farm in?"
                else:
                    plain = plain[:500].rsplit(" ", 1)[0].rstrip() + "…"

            # If the model produced a too-long English answer while language was selected, fallback language-safe text.
            if chosen_language == "Marathi" and any(x in plain.lower() for x in ["the ", "you can", "official link", "potentially relevant"]):
                if verified_matches:
                    s = verified_matches[0]
                    plain = f"{s['name']} तपासता येईल. पात्रता व वयोमर्यादा अधिकृत संकेतस्थळावर तपासा. तुमची शेती कोणत्या जिल्ह्यात आहे?"
                else:
                    plain = "तुम्हाला कोणत्या प्रकारची योजना हवी आहे—शेती, शिक्षण, आरोग्य की पेन्शन?"
            elif chosen_language == "Hindi" and any(x in plain.lower() for x in ["the ", "you can", "official link", "potentially relevant"]):
                if verified_matches:
                    s = verified_matches[0]
                    plain = f"{s['name']} देखी जा सकती है। पात्रता और उम्र की शर्तें आधिकारिक वेबसाइट पर जाँचें। आपका खेत किस ज़िले में है?"
                else:
                    plain = "आपको किसान, पढ़ाई, स्वास्थ्य या पेंशन में से किस तरह की योजना चाहिए?"

            save_transcript(clean_text, chosen_language)
            save_turn(clean_text, plain, chosen_language)
            self.history.append({"role": "assistant", "content": plain})
            self.history = self.history[-10:]
            return plain
        except Exception as exc:
            print(f"\n[JanSathi error] {type(exc).__name__}: {exc}")
            if chosen_language == "Marathi":
                return "माफ करा, आत्ता प्रश्न समजला नाही. कृपया थोडक्यात पुन्हा सांगा."
            if chosen_language == "Hindi":
                return "माफ़ कीजिए, सवाल समझ नहीं आया। कृपया थोड़ा धीरे फिर से बोलें."
            return "Sorry, I didn't catch that. Please try again, a little more slowly."
