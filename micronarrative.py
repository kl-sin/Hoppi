import os, traceback, json, base64
from together import Together

# Initialize Together API client
client = Together(api_key=os.getenv("TOGETHER_API_KEY", "").strip())

# Models
TEXT_MODEL = "openai/gpt-oss-20b"
IMAGE_MODEL = "black-forest-labs/FLUX.1-schnell"  # supports image generation


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
    Create 3 AI-generated images for each story beat.
    Converts base64 output from Together API into temporary files
    served via /download/<filename>.
    """
    image_urls = []

    for b in beats:
        try:
            img_prompt = f"{b['prompt']} | cinematic, natural light, detailed textures, poetic atmosphere"
            response = client.images.generate(
                model=IMAGE_MODEL,
                prompt=img_prompt,
                size="1024x1024",
                steps=8
            )

            print("[DEBUG RAW IMAGE RESPONSE]", response.__dict__)

            data = getattr(response, "data", [])
            if not data:
                raise ValueError("Empty image response")

            item = data[0]
            image_bytes = None

            # 🧩 Handle URL first, then base64 fallback
            if hasattr(item, "url") and item.url:
                image_urls.append({"title": b.get("title", ""), "url": item.url})
                continue  # ✅ Together returned a hosted image URL

            elif hasattr(item, "b64_json") and item.b64_json:
                image_bytes = base64.b64decode(item.b64_json)

            elif isinstance(item, dict):
                if "url" in item and item["url"]:
                    image_urls.append({"title": b.get("title", ""), "url": item["url"]})
                    continue
                elif "b64_json" in item and item["b64_json"]:
                    image_bytes = base64.b64decode(item["b64_json"])


            # 🖼️ Save image to /tmp
            if image_bytes:
                import uuid
                filename = f"story_{uuid.uuid4().hex}.png"
                path = f"/tmp/{filename}"
                with open(path, "wb") as f:
                    f.write(image_bytes)
                image_url = f"/download/{filename}"
            else:
                image_url = "https://placekitten.com/512/512"

            image_urls.append({
                "title": b.get("title", ""),
                "url": image_url
            })

        except Exception as e:
            print(f"[ERROR] Image generation failed for {b.get('title','(unknown)')}: {e}")
            image_urls.append({
                "title": b.get("title", ""),
                "url": "https://placekitten.com/512/512"
            })

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
