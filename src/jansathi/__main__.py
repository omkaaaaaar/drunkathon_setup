from .agent import JanSathiAgent
from .settings import settings
from .inferex_client import InferexError

WELCOME = """
====================================
  JanSathi Voice AI — local MVP
====================================
This first version tests conversation flow in the terminal.
Use /quit to exit, /reset to restart, /language en|hi|mr to set language.
Do not enter Aadhaar numbers, OTPs, bank details, or other sensitive data.
"""


def main() -> None:
    agent = JanSathiAgent()
    print(WELCOME)
    print(f"Mode: {'MOCK (no API calls)' if settings.mock_mode else 'LIVE InferexAI API'}")
    print("JanSathi: Namaste! I can help you discover government schemes. Which state do you live in, and what best describes you: student, farmer, employed, self-employed, or something else?")
    while True:
        try:
            user_text = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nJanSathi: Goodbye. Take care!")
            break
        if user_text.lower() in {"/quit", "/exit", "quit", "exit"}:
            print("JanSathi: Goodbye. Take care!")
            break
        if user_text.lower() == "/reset":
            agent = JanSathiAgent()
            print("JanSathi: Conversation restarted. Which state do you live in?")
            continue
        if user_text.lower().startswith("/language "):
            language = user_text.split(maxsplit=1)[1].strip().lower()
            if language in {"en", "hi", "mr"}:
                agent.language = language
                print(f"JanSathi: Language set to {language}. If using the live API, the model will be asked to respond in this language.")
            else:
                print("Use /language en, /language hi, or /language mr")
            continue
        try:
            answer = agent.respond(user_text)
            print(f"\nJanSathi> {answer}")
        except InferexError as exc:
            print(f"\nIntegration error: {exc}")
            print("Check .env and confirm API paths/model IDs with the teammate testing InferexAI.")
        except Exception as exc:
            print(f"\nUnexpected error: {exc}")

if __name__ == "__main__":
    main()
