
import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.environ["GROQ_API_KEY"])

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

SYSTEM_PROMPT = """
You are JanSathi, a multilingual assistant for discovering
government schemes in India.

Understand Marathi, Hindi and English.
Use the entire conversation to remember details the user
has already provided.
Never ask again for information already provided.

Extract the user's intent and profile.
Do not invent government schemes or eligibility rules.
Scheme eligibility must be checked by the Python application
against its supplied database.

Return JSON with exactly these fields:
{
  "intent": "discover_schemes | scheme_details | provide_information",
  "language": "mr | hi | en",
  "profile": {
    "state": null,
    "occupation": null,
    "age": null
  },
  "missing_fields": [],
  "response": "A short, natural response in the user's language"
}

Use null for unknown profile values.
Ask one useful follow-up question if necessary.
If enough information is available, explain the next step.
"""

def understand_conversation(messages: list[dict]) -> dict:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *messages,
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("Groq returned an empty response")

    result = json.loads(content)

    required = {
        "intent", "language", "profile",
        "missing_fields", "response"
    }
    if not required.issubset(result):
        raise ValueError("Groq response is missing required fields")

    return result
