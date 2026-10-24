from .agent import JanSathiAgent
from .settings import settings


def print_banner() -> None:
    print("=" * 36)
    print("  JanSathi Voice AI — local MVP")
    print("=" * 36)
    print("Terminal text prototype. Use /quit to exit, /reset to restart, /language en|hi|mr to set language.")
    print("Do not enter Aadhaar numbers, OTPs, bank details, or other sensitive data.\n")
    provider = settings.llm_provider.upper()
    if provider == "GROQ":
        print(f"LLM: Groq ({settings.groq_model})")
    elif provider == "inferex":
        print(f"LLM: InferexAI ({'MOCK' if settings.mock_mode else 'LIVE'})")
    else:
        print(f"LLM: {provider} (check LLM_PROVIDER configuration)")
    print(f"Voice services: {'MOCK / not connected' if settings.mock_mode else 'LIVE InferexAI configuration'}")
    print("Note: demo scheme records are illustrative and unverified.\n")


def main() -> None:
    print_banner()
    agent = JanSathiAgent()
    print("JanSathi: Namaste! I can help you explore government schemes. Which state do you live in, and what best describes you: student, farmer, employed, self-employed, or something else?\n")
    while True:
        try:
            user_text = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nJanSathi: Goodbye. Take care!")
            break
        if not user_text:
            continue
        command = user_text.lower()
        if command in {"/quit", "/exit"}:
            print("JanSathi: Goodbye. Take care!")
            break
        if command == "/reset":
            agent = JanSathiAgent()
            print("JanSathi: Conversation reset. Which state do you live in?\n")
            continue
        if command.startswith("/language "):
            language = command.split(maxsplit=1)[1]
            if language in {"en", "hi", "mr"}:
                agent.language = language
                print(f"JanSathi: Language preference set to {language}.\n")
            else:
                print("Use /language en, /language hi, or /language mr.\n")
            continue
        answer = agent.respond(user_text)
        print(f"\nJanSathi> {answer}\n")


if __name__ == "__main__":
    main()
