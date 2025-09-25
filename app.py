from flask import Flask, render_template, request, jsonify, send_file
import random
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Location-based tasks
TASKS_BY_LOCATION = {
    'park': [
        "Find the most interesting tree and take a selfie with it!",
        "Count how many different bird species you can spot in 5 minutes.",
        "Find a perfect spot for a picnic and document it.",
        "Take a photo of the most colorful flower you can find.",
        "Find a bench and write a haiku about the view."
    ],
    'restaurant': [
        "Order something you've never tried before and document the experience!",
        "Take a photo of your food from the most artistic angle possible.",
        "Find the most interesting person in the restaurant (respectfully) and imagine their story.",
        "Document the most unique item on the menu.",
        "Take a selfie with the most photogenic dish."
    ],
    'street': [
        "Find the most interesting street art or graffiti and photograph it.",
        "Count how many different colors you can spot in storefronts.",
        "Take a photo of the most unusual building or architecture.",
        "Find a street performer and document their performance.",
        "Look for the most creative shop window display."
    ],
    'beach': [
        "Build the most creative sandcastle you can and photograph it.",
        "Find the most interesting seashell and document your discovery.",
        "Take a photo of the waves from the most dramatic angle.",
        "Find a perfect spot to watch the sunset and document it.",
        "Look for the most colorful beach umbrella and take a selfie with it."
    ],
    'mall': [
        "Find the most interesting store display and photograph it.",
        "Take a selfie with the most unusual mannequin you can find.",
        "Document the most creative store name or logo.",
        "Find the most interesting food court item and photograph it.",
        "Look for the most unique piece of clothing and document it."
    ]
}

def get_location_type(lat, lon):
    """Simple location type detection based on coordinates"""
    # This is a simplified version - in reality you'd use reverse geocoding
    # For demo purposes, we'll use some basic logic
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        # Randomly assign location type for demo
        return random.choice(['park', 'restaurant', 'street', 'beach', 'mall'])
    return 'street'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/task', methods=['POST'])
def generate_task():
    try:
        data = request.get_json()
        lat = data.get('latitude')
        lon = data.get('longitude')
        
        if not lat or not lon:
            return jsonify({'error': 'Location data required'}), 400
        
        location_type = get_location_type(lat, lon)
        task = random.choice(TASKS_BY_LOCATION.get(location_type, TASKS_BY_LOCATION['street']))
        
        return jsonify({
            'task': task,
            'location_type': location_type,
            'coordinates': {'lat': lat, 'lon': lon}
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
