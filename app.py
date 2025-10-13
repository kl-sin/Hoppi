# /app/app.py
# Flask server (HF Spaces-safe: writes to /tmp by default)
from flask import Flask, render_template, request, jsonify, send_file
import os, json, uuid, random, traceback, requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from werkzeug.utils import secure_filename

# --- LLM client (safe fallback if llm.py absent) ---
try:
    from llm import prompt_llm
except Exception:
    def prompt_llm(prompt: str) -> str:  # minimal fallback; only used if llm.py missing
        return "Nice! That totally counts. Ready for another quick challenge?"

app = Flask(__name__)

# --- Writable paths (HF Spaces tip: /tmp is writable) ---
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', '/tmp/uploads')
RESULTS_DIR = os.getenv('RESULTS_DIR', '/tmp/results')

# 64 MB max upload
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024

# Ensure writable dirs exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# --- utils ---
def now_stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d-%H%M%S")

def http_get(url: str, **kw):
    kw.setdefault("timeout", 10)
    headers = kw.pop("headers", {})
    headers.setdefault("User-Agent", "hoppi-app")
    return requests.get(url, headers=headers, **kw)

def get_day_period(lat, lon):
    try:
        url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&formatted=0"
        res = http_get(url)
        res.raise_for_status()
        data = res.json()["results"]
        sunrise = datetime.fromisoformat(data["sunrise"]).replace(tzinfo=timezone.utc)
        sunset  = datetime.fromisoformat(data["sunset"]).replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)

        morning_end   = sunrise + timedelta(hours=4)
        afternoon_end = sunset  - timedelta(hours=2)

        if now < sunrise: return "pre-dawn"
        if sunrise <= now < morning_end: return "morning"
        if morning_end <= now < afternoon_end: return "afternoon"
        if afternoon_end <= now < sunset: return "evening"
        return "night"
    except Exception as e:
        print(f"[ERROR] Sunrise-Sunset API failed: {e}")
        hour = datetime.now().hour
        if hour < 12: return "morning"
        if hour < 18: return "afternoon"
        return "night"

def get_weather_hint(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        res = http_get(url)
        res.raise_for_status()
        data = res.json()
        weather_code = data["current_weather"]["weathercode"]
        if weather_code in (0,1): return "It's sunny, suggest something social and outdoors."
        if weather_code in (2,3,45): return "It's cloudy, suggest something cozy or introspective."
        if weather_code in (51,61,80): return "It's rainy, suggest something under shelter or with rain gear."
        if weather_code in (71,): return "It's snowy, suggest something fun with snow."
        return "Weather unclear; suggest something adaptable."
    except Exception as e:
        print(f"[Weather Error] {e}")
        return ""

def get_nearby_places(lat, lon, radius=500):
    url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    (
      node["leisure"="park"](around:{radius},{lat},{lon});
      node["leisure"="playground"](around:{radius},{lat},{lon});
      node["amenity"="cafe"](around:{radius},{lat},{lon});
      node["amenity"="restaurant"](around:{radius},{lat},{lon});
      node["amenity"="fast_food"](around:{radius},{lat},{lon});
      node["amenity"="bar"](around:{radius},{lat},{lon});
      node["amenity"="pub"](around:{radius},{lat},{lon});
      node["shop"="mall"](around:{radius},{lat},{lon});
      node["shop"="supermarket"](around:{radius},{lat},{lon});
      node["shop"="convenience"](around:{radius},{lat},{lon});
      node["amenity"="library"](around:{radius},{lat},{lon});
      node["amenity"="school"](around:{radius},{lat},{lon});
      node["amenity"="university"](around:{radius},{lat},{lon});
      node["amenity"="hospital"](around:{radius},{lat},{lon});
      node["amenity"="clinic"](around:{radius},{lat},{lon});
      node["amenity"="bus_station"](around:{radius},{lat},{lon});
      node["amenity"="train_station"](around:{radius},{lat},{lon});
      node["tourism"="museum"](around:{radius},{lat},{lon});
      node["tourism"="art_gallery"](around:{radius},{lat},{lon});
      node["leisure"="sports_centre"](around:{radius},{lat},{lon});
      node["leisure"="fitness_centre"](around:{radius},{lat},{lon});
      node["amenity"="place_of_worship"](around:{radius},{lat},{lon});
      node["amenity"="marketplace"](around:{radius},{lat},{lon});
      node["amenity"="theatre"](around:{radius},{lat},{lon});
      node["tourism"="hotel"](around:{radius},{lat},{lon});
    );
    out center;
    """
    try:
        res = http_get(url, params={'data': query})
        res.raise_for_status()
        data = res.json()
        elements = data.get('elements', [])
        out = []
        for el in elements:
            tags = el.get('tags', {})
            name = tags.get('name', 'Unknown place')
            category = tags.get('amenity') or tags.get('shop') or tags.get('leisure') or tags.get('tourism') or 'unknown'
            out.append({'name': name, 'category': category, 'lat': el.get('lat'), 'lon': el.get('lon')})
        return out
    except Exception as e:
        print(f"[ERROR] Nearby place detection failed: {e}")
        return []

def get_location_type(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=18&addressdetails=1"
        res = http_get(url)
        print(f"[DEBUG] Nominatim status {res.status_code}")
        data = res.json()
        tags = data.get("address", {})
        blob = json.dumps(tags).lower()
        if 'beach' in blob or 'coast' in blob: return 'beach'
        if 'park' in blob or tags.get('leisure','') == 'park': return 'park'
        if 'restaurant' in blob or 'cafe' in blob: return 'restaurant'
        if 'mall' in blob or 'shopping' in blob: return 'mall'
        if 'forest' in blob: return 'park'
        if any(k in tags for k in ('road','suburb','city','neighbourhood')): return 'street'
        return 'street'
    except Exception as e:
        print(f"[ERROR] Location type detection failed: {e}")
        return 'street'

def ensure_session_dir(session_id: str) -> Path:
    d = Path(app.config['UPLOAD_FOLDER']) / session_id
    d.mkdir(parents=True, exist_ok=True)
    return d

def next_index(session_dir: Path) -> int:
    dirs = [p for p in session_dir.iterdir() if p.is_dir() and p.name.isdigit()]
    return (max(int(p.name) for p in dirs)+1) if dirs else 1

def judge_submission(task: str, media_type: str, text: str | None, file_path: str | None, lat: float | None, lon: float | None) -> str:
    sample = f"User wrote: {text[:160]}" if (text and text.strip()) else (f"User submitted a {media_type}." if file_path else "No preview.")
    prompt = f"""
You are Hoppi, a playful, witty judge for real-world mini-challenges.
Task: {task}
Submission type: {media_type}
{sample}
Location: {lat}, {lon}

Rules:
- One short verdict (<= 35 words).
- Encouraging, specific, a little cheeky, never mean.
- Assume success if ambiguous.
- End with a nudge to do another task (no emojis/hashtags/bullets).
- No quotes or meta.
"""
    try:
        return prompt_llm(prompt).strip()
    except Exception as e:
        print("[LLM ERROR]", e)
        return "Nice! That totally counts. Ready for another quick challenge?"

# --- routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-task', methods=['POST'])
def generate_task():
    try:
        data = request.get_json(force=True)
        lat = data.get('latitude'); lon = data.get('longitude')
        if lat is None or lon is None:
            return jsonify({'error': 'Location data required'}), 400
        location_type = get_location_type(lat, lon)
        weather_hint = get_weather_hint(lat, lon)
        nearby_places = get_nearby_places(lat, lon)
        main_place = random.choice(nearby_places) if nearby_places else None

        period = get_day_period(lat, lon)
        time_hint_map = {
            "pre-dawn":"It's before sunrise — suggest something peaceful or introspective.",
            "morning":"It's morning, suggest something energizing and fresh.",
            "afternoon":"It's afternoon, suggest something social or creative.",
            "evening":"It's evening, suggest something calm and reflective.",
            "night":"It's night, suggest something quiet, safe, and introspective."
        }
        safety_hint = "It's dark, so avoid unsafe areas or strangers. Focus on calm, personal tasks." if period in ("evening","night","pre-dawn") else "It's bright outside, so social or playful tasks are great."
        nearby_hint = f"There is a {main_place['category']} nearby called '{main_place['name']}'. Suggest something relevant to that place." if main_place else "No major places nearby. Suggest something suitable for open areas."
        daytime = [
            "Be energetic and playful.","Encourage interaction with others.","Make it involve a stranger.",
            "Encourage them to take a photo, video or record audio.","Make it feel like a mini-game.",
            "Include movement or interaction with the environment.","Encourage a quick creative act.",
            "Make them explore a small detail around them they normally ignore.","Include something involving color or sound."
        ]
        nighttime = [
            "Be soft and gentle.","Encourage quiet reflection.","Focus on creativity or mindfulness.",
            "Suggest a calming or self-reflective act.","Make it about observing surroundings quietly.",
            "Encourage them to write or record a thought privately.","Let them notice city lights, sounds, or patterns quietly.",
            "Prompt them to capture a subtle night detail in a photo or note."
        ]
        variation_hint = random.choice(nighttime if period in ("evening","night","pre-dawn") else daytime)
        freshness_hint = random.choice([
            "Make sure this challenge feels totally new compared to any previous idea.",
            "Ensure this activity feels distinct in tone or action from the last few suggestions.",
            "Add a small creative twist not seen in previous tasks.",
            "Vary the setting or mood slightly to keep it interesting.",
            "Change up the interaction style for variety."
        ])

        prompt = f"""
You are a warm, witty real-world assistant named Hoppi.

The user’s environment: {location_type}.
Coordinates: {lat:.4f}, {lon:.4f}.
Local time (approx hour): {datetime.now().strftime('%H')}:00.
{weather_hint}
According to the sun cycle, it’s {period}.
{time_hint_map[period]}
{safety_hint}

Nearby info: {nearby_hint}
Variation: {variation_hint}
Freshness: {freshness_hint}

Write ONE short, fun, real-time challenge under 30 words.
No emojis/hashtags. Avoid repetitive openings. No exact clock time. Simple, 12-year-old-friendly, spontaneous, doable now with just a phone.
"""
        # Write last prompt for debugging/QA (in writable place)
        os.makedirs(RESULTS_DIR, exist_ok=True)
        with open(os.path.join(RESULTS_DIR, 'prompts.txt'), 'w', encoding='utf-8') as f:
            f.write(prompt + "\n")

        task = prompt_llm(prompt).strip()
        return jsonify({
            'task': task,
            'location_type': location_type,
            'coordinates': {'lat': lat, 'lon': lon},
            'source': "LLM",
            'selected_place': main_place
        })
    except Exception as e:
        print("[ERROR] Exception in generate-task:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route("/submit", methods=["POST"])
def submit():
    try:
        session_id = request.form.get("session_id") or str(uuid.uuid4())
        task = (request.form.get("task") or "").strip()
        media_type = (request.form.get("media_type") or "").strip()
        lat = request.form.get("lat", type=float)
        lon = request.form.get("lon", type=float)
        text = request.form.get("text")

        if not task or not media_type:
            return jsonify({"error":"Missing task or media_type"}), 400

        sdir = ensure_session_dir(session_id)
        idx = next_index(sdir)
        entry = sdir / f"{idx:03d}"
        entry.mkdir(parents=True, exist_ok=True)

        file_path = None
        if "file" in request.files and request.files["file"].filename:
            f = request.files["file"]
            fname = secure_filename(f.filename) or f"{media_type}-{now_stamp()}"
            file_path = str(entry / fname)
            f.save(file_path)

        if text and text.strip():
            (entry / "note.txt").write_text(text.strip(), encoding="utf-8")

        meta = {
            "session_id": session_id, "index": idx, "task": task, "media_type": media_type,
            "file": file_path, "text": (text or ""), "lat": lat, "lon": lon,
            "created_utc": datetime.utcnow().isoformat() + "Z",
        }
        (entry / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

        total = len([p for p in sdir.iterdir() if p.is_dir() and p.name.isdigit()])
        remaining = max(0, 5 - total)
        surprise_ready = total >= 5

        judge_text = judge_submission(task, media_type, text, file_path, lat, lon)

        return jsonify({"ok": True, "session_id": session_id, "count": total, "remaining": remaining, "surprise_ready": surprise_ready, "judge_text": judge_text})
    except Exception as e:
        print("[ERROR] /submit failed", traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/progress/<session_id>", methods=["GET"])
def progress(session_id: str):
    try:
        sdir = ensure_session_dir(session_id)
        total = len([p for p in sdir.iterdir() if p.is_dir() and p.name.isdigit()])
        return jsonify({"count": total, "remaining": max(0, 5 - total), "surprise_ready": total >= 5})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<path:filename>')
def download_file(filename):
    try:
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(path):
            return send_file(path, as_attachment=True)
        return jsonify({'error':'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    # On local runs you can override PORT; HF sets PORT automatically.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=True)
