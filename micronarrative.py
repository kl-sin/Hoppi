import os, traceback, json, urllib.parse
from together import Together

# Initialize Together API client
client = Together(api_key=os.getenv("TOGETHER_API_KEY", "").strip())

# Models
TEXT_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
# Images are generated via Pollinations (free, no API key) — see generate_story_images()


def submissions_are_unrelated(submissions):
    """Heuristic check for whether the 3 submissions share little or no thematic overlap."""
    text_blob = " ".join(s.get("summary", "") for s in submissions if s.get("summary"))
    if len(text_blob.strip()) < 30:
        return True
    keywords = [w.lower() for w in text_blob.split()]
    unique_ratio = len(set(keywords)) / max(len(keywords), 1)
    return unique_ratio > 0.9  # high uniqueness = low coherence


def generate_micro_narrative(submissions):
    """
    Turn 3 submissions into a short 3-part visual micro-narrative.
    Each submission = {task, summary, judge_feedback}
    """
    joined = "\n\n".join([
        f"Task: {s['task']}\nSubmission: {s.get('summary','')}\nHoppi's feedback: {s.get('judge_feedback','')}"
        for s in submissions
    ])

    unrelated = submissions_are_unrelated(submissions)
    if unrelated:
        narrative_hint = (
            "These three submissions seem unrelated. Don’t force a plot. "
            "Instead, create a playful snapshot that shows contrast — like flipping through someone’s curious day. "
            "Keep it light, simple, and grounded."
        )
    else:
        narrative_hint = (
            "These three moments share a loose connection. Write a short, human mini-story that links them together. "
            "Make it sound like someone casually describing what happened to a friend."
        )

    prompt = f"""
You are Hoppi — a micro-narrative storyteller.
{narrative_hint}

Write a micro-narrative under 60 words that connects or reinterprets these 3 user submissions.
Your tone should be light, clear, human, and a bit thoughtful — not poetic or abstract.
Do NOT mention specific times of day (like 8am, 4:15am, etc.).
Focus on small actions, textures, or emotions shared between the moments.

Then generate 3 short visual prompts — one per moment — based on the story’s key scenes.
When creating visual prompts, do not add specific times of day unless clearly implied by the submissions themselves.

Format your output as JSON:
{{
  "story_text": "...",
  "beats": [{{"title":"...","prompt":"..."}}, ...]
}}

Submissions:
{joined}

Return ONLY JSON.
"""

    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        text_out = response.choices[0].message.content.strip()

        # --- Safe JSON parsing ---
        try:
            data = json.loads(text_out)
        except json.JSONDecodeError:
            print("[WARN] Model returned non-JSON, trying to fix...")
            text_out = text_out[text_out.find("{"):text_out.rfind("}")+1]
            data = json.loads(text_out)

        story_text = data.get("story_text", "").strip()
        beats = data.get("beats", [])

        if unrelated and not beats:
            beats = [
                {"title": "Fragment I", "prompt": "abstract swirl of lights and motion blur"},
                {"title": "Fragment II", "prompt": "floating memories in pastel mist"},
                {"title": "Fragment III", "prompt": "gentle horizon fading into cosmic noise"}
            ]

        return story_text, beats

    except Exception:
        print("[ERROR] Narrative text generation failed:", traceback.format_exc())
        story_text = "Three quiet moments stitched together — a small journey seen through curious eyes."
        beats = [
            {"title": "Scene 1", "prompt": "soft morning light over an urban corner"},
            {"title": "Scene 2", "prompt": "vivid colors and textures noticed mid-day"},
            {"title": "Scene 3", "prompt": "evening calm under city lights"}
        ]
        return story_text, beats


def generate_story_images(beats):
    """
    Build one AI-image URL per story beat using Pollinations
    (free, no API key). The browser loads each URL directly and the
    image is generated on demand — no server-side download needed.
    """
    image_urls = []

    for i, b in enumerate(beats):
        try:
            img_prompt = f"{b.get('prompt','')} | cinematic, natural light, detailed textures, poetic atmosphere"
            encoded = urllib.parse.quote(img_prompt)
            # `seed` keeps each beat's image stable/distinct; nologo removes watermark
            url = (
                f"https://image.pollinations.ai/prompt/{encoded}"
                f"?width=1024&height=1024&nologo=true&seed={i}"
            )
            image_urls.append({"title": b.get("title", ""), "url": url})
        except Exception as e:
            print(f"[ERROR] Image URL build failed for {b.get('title','(unknown)')}: {e}")
            # picsum is a live placeholder (unlike the retired placekitten)
            image_urls.append({"title": b.get("title", ""), "url": "https://picsum.photos/1024"})

    print("[DEBUG] Generated story images:", image_urls)
    return image_urls


def create_micro_narrative_chapter(submissions):
    """
    High-level pipeline: 3 submissions → narrative text + 3 generated images
    """
    story_text, beats = generate_micro_narrative(submissions)
    image_urls = generate_story_images(beats)
    return {
        "story_text": story_text,
        "beats": beats,
        "images": image_urls
    }
