import os
import time

from dotenv import load_dotenv
from groq import Groq, RateLimitError

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Fast model for most tasks, strong model for synthesis
DEFAULT_MODEL = "openai/gpt-oss-20b"
STRONG_MODEL = "openai/gpt-oss-120b"


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = DEFAULT_MODEL,
    max_retries: int = 3,
) -> str:
    last_error = None
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content
        except RateLimitError as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)  # 2s, 4s, 8s
                print(f"  [rate limit] retrying in {wait}s...")
                time.sleep(wait)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(1)

    raise last_error


def call_llm_strong(system_prompt: str, user_prompt: str) -> str:
    """Use the stronger model for synthesis."""
    return call_llm(system_prompt, user_prompt, model=STRONG_MODEL)
