import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

response = client.chat.completions.create(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
    messages=[
        {
            "role": "user",
            "content": "Reply in Marathi with one short greeting."
        }
    ],
)

print(response.choices[0].message.content)