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
# 🧩 ADD THIS DEBUG LINE HERE:
print(f"[DEBUG] TOGETHER_API_KEY exists: {bool(TOGETHER_API_KEY)}")

client = Together(api_key=TOGETHER_API_KEY)

def prompt_llm(prompt, with_linebreak=False):
    model = "openai/gpt-oss-20b"
    print(f"[DEBUG] Sending prompt to Together API (model={model})")

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    output = response.choices[0].message.content
    print(f"[DEBUG] LLM response received: {output[:80]}...")  # shorten for logs

    return textwrap.fill(output, width=50) if with_linebreak else output
