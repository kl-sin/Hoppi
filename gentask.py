# suppress warnings
import warnings
warnings.filterwarnings("ignore")

import os
import textwrap
from dotenv import load_dotenv
from together import Together

# Load environment variables (for local dev)
load_dotenv()

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "").strip()
print(f"[DEBUG] TOGETHER_API_KEY exists: {bool(TOGETHER_API_KEY)}")

client = Together(api_key=TOGETHER_API_KEY)

# Together serverless models this account can reach, tried in order.
# The first that returns non-empty text wins, so the app keeps working
# when a single model is temporarily unavailable (503) or returns empty.
CHAT_MODELS = [
    "meta-llama/Llama-3.3-70B-Instruct-Turbo",  # fast, returns text directly
    "openai/gpt-oss-120b",                       # reasoning model; needs budget
]


def chat(prompt, with_linebreak=False):
    """Send a prompt to the first available chat model and return its text.

    Tries each model in CHAT_MODELS until one returns non-empty content.
    Raises RuntimeError only if every model fails.
    """
    last_err = None
    for model in CHAT_MODELS:
        try:
            kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                # headroom so reasoning models (gpt-oss) still emit text after
                # their internal reasoning instead of running out of tokens
                "max_tokens": 1200,
            }
            if "gpt-oss" in model:
                kwargs["reasoning_effort"] = "low"

            print(f"[DEBUG] Sending prompt to Together API (model={model})")
            resp = client.chat.completions.create(**kwargs)
            output = (resp.choices[0].message.content or "").strip()

            if output:
                print(f"[DEBUG] LLM response via {model}: {output[:80]}...")
                return textwrap.fill(output, width=50) if with_linebreak else output

            print(f"[WARN] {model} returned empty content, trying next model")
        except Exception as e:
            last_err = e
            print(f"[WARN] model {model} failed: {e}")

    raise RuntimeError(f"All chat models failed; last error: {last_err}")


# Back-compat alias used across the app
def prompt_llm(prompt, with_linebreak=False):
    return chat(prompt, with_linebreak)
