import os, random, json, re
from dotenv import load_dotenv
from together import Together

load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "").strip()
client = Together(api_key=TOGETHER_API_KEY)

MODEL = "google/gemma-3n-E4B-it"

def summarize_media(file_path, media_type):
    if not file_path:
        return "No file provided."

    # --- 1️⃣ Image analysis ---
    if media_type in ("photo", "image", "picture"):
        try:
            # Example with a local captioning model or API
            import requests
            caption_res = requests.post(
                "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large",
                headers={"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"},
                files={"file": open(file_path, "rb")},
                timeout=20
            )
            caption_data = caption_res.json()
            if isinstance(caption_data, list) and "generated_text" in caption_data[0]:
                caption = caption_data[0]["generated_text"]
            elif isinstance(caption_data, dict) and "generated_text" in caption_data:
                caption = caption_data["generated_text"]
            else:
                caption = str(caption_data)

            return f"Image description: {caption}"
        except Exception as e:
            print("[WARN] Image captioning failed:", e)
            return "Image description unavailable."

    # --- 2️⃣ Audio transcription ---
    elif media_type in ("audio", "recording", "voice"):
        try:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")
            transcript = openai.Audio.transcribe("whisper-1", open(file_path, "rb"))
            return f"Audio transcription: {transcript['text']}"
        except Exception as e:
            print("[WARN] Audio transcription failed:", e)
            return "Audio content unavailable."

    # --- 3️⃣ Fallback for video or others ---
    elif media_type == "video":
        return "Video uploaded — not analyzed yet."
    else:
        return "Unsupported media type."

def judge_with_gemma(task, media_type, text=None, file_path=None, lat=None, lon=None, session_id=None, context=None):
    """Hoppi's dynamic judge — concise, witty, and task-aware."""

    sample = f"User wrote: {text[:200]}" if text else f"User submitted a {media_type}."
    location_hint = context.get("location_type") if context else None
    weather_hint = context.get("weather_hint") if context else None
    day_period = context.get("day_period") if context else None

    tone_hint = {
        "morning": "be bright and energizing",
        "afternoon": "sound playful and social",
        "evening": "be warm and reflective",
        "night": "be calm, witty, and gentle",
    }.get(day_period, "be upbeat and kind")

    humor_style = random.choice(["playful", "clever", "lightly teasing", "curious and kind"])

    # 🎯 Task-aware, clean, and direct prompt
    prompt = f"""
You are Hoppi — a witty, thoughtful AI who is a story companion, not just a reviewer

Task:
> {task}

User submission:
> {sample}

Environment context:
- Media type: {media_type}
- Location: {location_hint}, {weather_hint}
- Time: {day_period}
- Tone: {tone_hint}
- Humor: {humor_style}

Your goal:
1. Skip greetings like “Hello there” or “Hi friend.”
2. Be short, friendly, and specific (under 45 words).
3. Naturally describe what the user’s submission makes you imagine or feel, not just what it “is.”
4. If the submission doesn’t fit the task, react creatively: connect it to the moment or mood instead of rejecting it outright. Example: “That wasn’t quite about sound, but it feels like a secret waiting to be heard.
5. Avoid generic compliments (“Beautiful!” “Nice work!”). Focus on imagery, tone, or emotion evoked.
6. Always close with a single line that feels like a narrative handoff, e.g. “The story continues — shall we see what’s next?”
7. No emojis, hashtags, lists, or markdown.

Example responses:
A. If slightly off-topic:

→ Reframe it creatively.

“That’s a different angle than I expected, but it feels like a small rebellion — and that’s part of the fun.”

B. If totally irrelevant (e.g., random photo when asked for audio):

→ Keep tone forgiving, fold it back into the “world” of the app.

“Hmm, that doesn’t quite match the challenge, but it adds a mysterious glitch to our story. Let’s keep it — every adventure needs one.”

C. If clearly empty or meaningless input:

→ Encourage re-engagement gently.

“Looks like a blank moment — maybe Hoppi blinked? Try another quick capture and let’s see what story spark shows up.”

Now write your response as Hoppi.
"""

    try:
        print(f"[DEBUG] Sending judge prompt to Together API (model={MODEL})")
        print(f"[DEBUG] Prompt preview:\n{prompt[:200]}...\n")

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        text_out = response.choices[0].message.content.strip()
        print("[DEBUG] Judge model response received:", text_out[:200], "...\n")

    except Exception as e:
        print("[GEMMA ERROR]", e)
        return "That was unexpected — but Hoppi loves surprises! Ready for another quick challenge?"

    # 🧹 Clean up and tighten
    match = re.search(r'"feedback"\s*:\s*"([^"]+)"', text_out)
    if match:
        feedback = match.group(1)
    else:
        feedback = text_out
    feedback = feedback.strip().replace("\n", " ")

    # ✂️ Limit to ~45 words
    feedback_words = feedback.split()
    if len(feedback_words) > 45:
        feedback = " ".join(feedback_words[:45]) + "…"

    # 💬 Ensure only one encouragement line
    encouragements = [
        "Ready for another little adventure?",
        "Want to see what Hoppi dreams up next?",
        "Shall we try another quick challenge?",
        "Let’s cook up the next idea!",
    ]
    if not any(e.split("?")[0] in feedback for e in encouragements):
        feedback = feedback.rstrip(".!?") + ". " + random.choice(encouragements)

    return feedback
