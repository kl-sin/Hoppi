from flask import Flask, render_template, request, jsonify, send_file
import random
import os
import requests   # 👈 add this line
from werkzeug.utils import secure_filename
from llm import prompt_llm
from functools import lru_cache
from datetime import datetime


# Simple in-memory cache for repeated prompts (reset on server restart)
# @lru_cache(maxsize=10)
def get_cached_task_for_location(location_type, lat=None, lon=None):
    try:
        # 🌞 Time of day
        hour = datetime.now().hour
        if hour < 12:
            time_hint = "It's morning, suggest something energizing."
        elif hour < 17:
            time_hint = "It's afternoon, suggest something social."
        else:
            time_hint = "It's evening, suggest something reflective or relaxing."

        # 🌙 Safety considerations (NEW — add this right after time detection)
        if hour >= 19 or hour < 6:  # 8PM–6AM
            safety_hint = (
                "It's nighttime, so avoid tasks involving strangers or dark areas. "
                "Focus on calm, solo, or reflective activities instead."
            )
        else:
            safety_hint = "It's daytime, so interactive and social tasks are fine."
            
        # 🌦 Weather condition
        weather_hint = ""
        if lat is not None and lon is not None:
            weather_hint = get_weather_hint(lat, lon)
            print(f"[DEBUG] Weather hint: {weather_hint}")  # 👈 ADD THIS LINE HERE

        # 🎲 Add variation to keep tasks fresh
        variation_hint = random.choice([
            "Make it involve a stranger.",
            "Encourage them to take a photo.",
            "Make it feel like a mini-game.",
            "Include movement or interaction with the environment.",
            "Encourage a quick creative act."
        ])

        # 🧠 Final prompt
        prompt = (
    f"You are a playful assistant generating real-world micro-challenges.\n"
    f"The user is in a {location_type} environment.\n"
    f"Current time of day: {datetime.now().strftime('%H:%M')}.\n"
    f"{time_hint}\n"
    f"{weather_hint}\n"
    f"{safety_hint}\n"     # 👈 add this line
    f"{variation_hint}\n"
    f"Based on this context, generate a **new**, unique, and fun challenge they can do now.\n"
    f"The task should feel appropriate for the environment and conditions.\n"
    f"Keep it concise (1 sentence), easy to understand, and suitable for someone walking outside.\n"
    f"Do not repeat ideas you've given before. Avoid using emojis or hashtags.\n"
    f"Their coordinates are approximately {lat:.4f}, {lon:.4f}.\n"
    f"Ensure this task is **different** from previous ones in style or action."
)


        # Save prompt for inspection
        os.makedirs('results', exist_ok=True)
        with open('results/prompts.txt', 'w') as f:
            f.write(prompt + "\n")

        task = prompt_llm(prompt)
        return task.strip()
    
    except Exception as e:
        print(f"[ERROR] Prompt generation failed: {e}")
        return None # Will trigger fallback

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Location-based tasks with social and creative elements
TASKS_BY_LOCATION = {
    'park': [
        "🌳 Hug a tree and ask a stranger or friend to take your photo!",
        "🍃 Create a beautiful pattern using fallen leaves and photograph it.",
        "🎵 Find a stranger and ask them to sing a simple beat with you (clap, snap, or hum).",
        "📹 Record a 30-second video of you doing your best tree impression.",
        "🌿 Collect 5 different types of leaves and arrange them artistically for a photo.",
        "🎶 Find someone walking their dog and ask them to join you in a silly song about their pet.",
        "📱 Take a video of you teaching a stranger how to identify 3 different trees.",
        "🌺 Create a flower crown and ask someone to take a photo of you wearing it.",
        "🎤 Record yourself singing a nature-themed song while walking through the park.",
        "🤝 Find a stranger and ask them to help you build a tiny fairy house with natural materials."
    ],
    'restaurant': [
        "🍽️ Order something you've never tried and ask a stranger to guess what it is!",
        "🎵 Create a beat using your utensils and ask someone to join in.",
        "📹 Record a video of you doing a dramatic food review for the camera.",
        "🎤 Sing a song about the food you're eating and ask a stranger to rate it.",
        "📱 Take a video of you teaching someone how to eat the most interesting dish on your table.",
        "🤝 Find someone dining alone and ask them to join you for a fun food challenge.",
        "🎶 Ask the waiter to help you create a silly song about the restaurant's specialty.",
        "📸 Take a selfie with the chef and ask them to tell you their favorite cooking tip.",
        "🎵 Use your phone to play a beat and ask a stranger to freestyle rap about their meal.",
        "📹 Record a video of you doing a taste test blindfolded with a stranger's help."
    ],
    'street': [
        "🎨 Find street art and ask a stranger to pose with it for a creative photo.",
        "🎵 Start a beat by clapping and see how many people join in!",
        "📹 Record a video of you doing your best street performer impression.",
        "🎤 Sing a song about the street you're on and ask someone to add a verse.",
        "📱 Take a video of you asking strangers to guess what's in a mystery bag.",
        "🤝 Find someone waiting for a bus and ask them to help you create a sidewalk chalk drawing.",
        "🎶 Ask a street musician to teach you a simple melody and record it.",
        "📸 Take a selfie with a stranger and ask them to tell you their life story in one sentence.",
        "🎵 Create a beat using sounds from the street (footsteps, car horns, etc.) and record it.",
        "📹 Record a video of you doing a street dance and ask someone to join you."
    ],
    'beach': [
        "🏖️ Build a sandcastle and ask a stranger to help you decorate it!",
        "🎵 Create a rhythm using seashells and ask someone to join your beach band.",
        "📹 Record a video of you doing your best mermaid impression in the sand.",
        "🎤 Sing a beach-themed song and ask someone to harmonize with you.",
        "📱 Take a video of you teaching a stranger how to find the perfect seashell.",
        "🤝 Find someone building sand art and ask them to collaborate on a masterpiece.",
        "🎶 Ask a stranger to help you write a song about the ocean and record it.",
        "📸 Take a selfie with a stranger and ask them to share their favorite beach memory.",
        "🎵 Use the waves as a beat and ask someone to freestyle rap about summer.",
        "📹 Record a video of you doing a beach yoga pose and ask someone to join you."
    ],
    'mall': [
        "🛍️ Find a stranger and ask them to help you pick the most outrageous outfit!",
        "🎵 Create a beat using items from different stores and ask someone to join in.",
        "📹 Record a video of you doing a fashion show walk and ask someone to judge it.",
        "🎤 Sing a shopping-themed song and ask a stranger to add a verse about their favorite store.",
        "📱 Take a video of you asking strangers to guess what's in your shopping bag.",
        "🤝 Find someone at the food court and ask them to help you create a food art masterpiece.",
        "🎶 Ask a store employee to teach you their store's jingle and record it.",
        "📸 Take a selfie with a stranger and ask them to tell you their shopping secret.",
        "🎵 Use the mall's ambient sounds to create a beat and ask someone to dance to it.",
        "📹 Record a video of you doing a mall walk and ask someone to join your fitness challenge."
    ]
}


def get_weather_hint(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        res = requests.get(url)
        data = res.json()
        weather_code = data["current_weather"]["weathercode"]

        # See: https://open-meteo.com/en/docs for full code meanings
        weather_conditions = {
            0: "clear sky",
            1: "mainly clear",
            2: "partly cloudy",
            3: "overcast",
            45: "fog",
            48: "depositing rime fog",
            51: "light drizzle",
            61: "light rain",
            71: "light snow",
            80: "rain showers",
        }

        description = weather_conditions.get(weather_code, "unknown conditions")

        if weather_code in [0, 1]:
            return "It's sunny, suggest something social and outdoors."
        elif weather_code in [2, 3, 45]:
            return "It's cloudy, suggest something cozy or introspective."
        elif weather_code in [51, 61, 80]:
            return "It's rainy, suggest something under shelter or with rain gear."
        elif weather_code in [71]:
            return "It's snowy, suggest something fun with snow."
        else:
            return f"The weather is {description}, suggest something suitable."
    except Exception as e:
        print(f"[Weather Error] {e}")
        return ""


def get_location_type(lat, lon):
    import requests

    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&zoom=18&addressdetails=1"
        res = requests.get(url, headers={"User-Agent": "hoppi-app"})
        data = res.json()
        tags = data.get("address", {})
        
        if 'beach' in str(tags).lower() or 'coast' in str(tags).lower():
            return 'beach'
        elif 'park' in tags.get('leisure', '') or 'park' in str(tags).lower():
            return 'park'
        elif 'restaurant' in str(tags).lower() or 'cafe' in str(tags).lower():
            return 'restaurant'
        elif 'mall' in str(tags).lower() or 'shopping' in str(tags).lower():
            return 'mall'
        elif 'forest' in str(tags).lower():
            return 'park'
        elif 'road' in tags or 'suburb' in tags or 'city' in tags:
            return 'street'
        else:
            return 'street'
    except Exception as e:
        print(f"Location type detection failed: {e}")
        return 'street'


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-task', methods=['POST'])
def generate_task():
    try:
        data = request.get_json()
        lat = data.get('latitude')
        lon = data.get('longitude')

        if not lat or not lon:
            return jsonify({'error': 'Location data required'}), 400

        location_type = get_location_type(lat, lon)

        # First, try LLM (cached)
        task = get_cached_task_for_location(location_type, lat, lon)

        # Track source
        source = "LLM"

        # Fallback if LLM failed
        if not task:
            task = random.choice(TASKS_BY_LOCATION.get(location_type, TASKS_BY_LOCATION['street']))
            source = "fallback"

        return jsonify({
            'task': task,
            'location_type': location_type,
            'coordinates': {'lat': lat, 'lon': lon},
            'source': source  # 👈 this tells you where the task came from
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            return jsonify({
                'message': 'Image uploaded successfully',
                'filename': filename,
                'filepath': filepath
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

