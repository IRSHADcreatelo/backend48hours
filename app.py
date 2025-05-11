from flask import Flask, request, jsonify, make_response, render_template
from flask_cors import CORS
import uuid
import requests
import os

app = Flask(__name__)
# Configure CORS to allow requests from Vercel frontend (update with actual frontend URL after deployment)
CORS(app, resources={r"/api/*": {"origins": ["https://frontend48.vercel.app/", "http://localhost:8000"]}})

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set")
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent'

# Function to generate brand story using Gemini API via URL
def generate_brand_story(name, website, tagline):
    try:
        # Sanitize inputs
        name = name.strip()
        website = website.strip()
        tagline = tagline.strip()

        # Define the prompt for Gemini
        prompt = (
            f"Create a compelling brand story for a company named '{name}' with the website '{website}' "
            f"and tagline '{tagline}'. The story should be engaging, concise (100-150 words), and highlight "
            f"the brand's mission, values, and unique qualities. Ensure the tone is professional yet inspiring."
        )

        # Prepare the payload for the API request
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }

        # Make the API request
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            json=payload,
            headers=headers
        )

        # Check for successful response
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                text = result['candidates'][0]['content']['parts'][0]['text']
                return text.strip()
            else:
                raise Exception("No valid content in API response")
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")

    except Exception as e:
        raise Exception(f"Error generating brand story: {str(e)}")

# Route for generating brand story
@app.route('/api/generate-story', methods=['POST'])
def generate_story():
    try:
        data = request.get_json()
        if not data or not all(key in data for key in ['name', 'website', 'tagline']):
            return jsonify({'error': 'Missing required fields'}), 400

        name = data['name']
        website = data['website']
        tagline = data['tagline']

        # Generate unique session ID and set cookie
        session_id = str(uuid.uuid4())
        story = generate_brand_story(name, website, tagline)

        response = make_response(jsonify({'story': story}))
        response.set_cookie('session_id', session_id, max_age=3600, httponly=True, samesite='Strict', secure=True)
        return response

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handling route
@app.route('/error')
def error():
    return render_template('error.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
