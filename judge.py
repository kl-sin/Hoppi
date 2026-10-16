import os, random, json, re
from dotenv import load_dotenv
from together import Together

load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "").strip()
client = Together(api_key=TOGETHER_API_KEY)

MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo"

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

    sample = f"User wrote: {text[:200]}" 
    if text:
        sample = f"User wrote: {text[:200]}"
    elif file_path:
        sample = summarize_media(file_path, media_type)
    else:
        sample = f"A {media_type} was submitted, but no further detail was provided."

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
2. Be short, friendly, and specific (under 30 words).
3. React to the actual content first — summarize or interpret what the user submitted (especially audio or image content), even if it diverges from the task.
4. Use surprise or contrast. Point out what’s weird, bold, or interesting in what they did.
5. If it’s off-task: tease them a little, but make it fun — like “that’s not what I asked, but I’ll allow it.”
6. Avoid generic compliments (“Beautiful!” “Nice work!”). Focus on imagery, tone, or emotion evoked.
7. No emojis, hashtags, lists, or markdown.
8. Be playful and teasing — like a clever friend noticing what they *tried* to do.

Examples:

A. User sends breath audio as requested:
> “Alright, that’s definitely breathing. Not creepy at all. You and the BUDō door are totally vibing. Want the next one?”

B. User sends something random instead of breath:
> “That’s not a breath. That’s... a glitchy rave? But sure, let’s pretend it’s your soul pulsing at 6am. Let’s see what’s next.”

C. User nails the mood:
> “Oooh that clip is so calm I almost took a nap. You’re setting the mood early. Ready to shake it up?”

D. Totally empty or meaningless input:
> “You blinked, didn’t you? Try again — I want to hear something real.”

Rules:
- Be short (under 30 words).
- Be specific, casual, and grounded.
- No greetings, hashtags, or quotes.
- Always react to the submission. Never ignore it.
- Keep the voice smart, warm, and just a little chaotic.
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
