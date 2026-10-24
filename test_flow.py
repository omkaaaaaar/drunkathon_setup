
import json
from dotenv import load_dotenv

from jansathi.groq_client import understand_conversation
from jansathi.storage import load_schemes, save_transcript, save_turn
from jansathi.scheme_matcher import match_schemes

load_dotenv()

messages = [
    {"role": "user", "content": "मला शेतकऱ्यांसाठी सरकारी योजना सांगा."},
    {"role": "assistant", "content": "तुम्ही कोणत्या राज्यात राहता?"},
    {"role": "user", "content": "मी महाराष्ट्रातील शेतकरी आहे."},
]

latest_text = messages[-1]["content"]
save_transcript(latest_text, "mr")

# Ask Groq to understand the conversation
result = understand_conversation(messages)

# Use details extracted by Groq
profile = {
    "state": "Maharashtra",
    "occupation": "farmer",
    "age": None,
}

for key, value in result["profile"].items():
    if value is not None:
        profile[key] = value

# Match against our local demo database
schemes = load_schemes()
matches = match_schemes(schemes, profile)

print("\n--- Groq understanding ---")
print(json.dumps(result, ensure_ascii=False, indent=2))

print("\n--- Demo scheme matches ---")
for scheme in matches:
    print("-", scheme["name"], "(illustrative data; not verified)")

answer = result["response"]

if matches:
    answer += "\nDemo schemes to explore: " + ", ".join(
        scheme["name"] for scheme in matches
    )

print("\nJanSathi:", answer)

save_turn(latest_text, answer, result["language"])
