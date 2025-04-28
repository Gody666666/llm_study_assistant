from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import requests
import base64
import json
from typing import List, Dict
import os

app = Flask(__name__)
CORS(app)

OLLAMA_API_URL = "http://localhost:11434"

def get_available_models() -> List[Dict]:
    """Get list of available models from Ollama"""
    try:
        response = requests.get(f"{OLLAMA_API_URL}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [
                {
                    "name": model["name"],
                    "supportsVision": "vision" in model["name"].lower()
                }
                for model in models
            ]
    except Exception as e:
        print(f"Error fetching models: {e}")
    return []

@app.route('/api/models', methods=['GET'])
def models():
    """Get available models"""
    return jsonify(get_available_models())

def encode_image_to_base64(image_data: bytes) -> str:
    """Encode image data to base64"""
    return base64.b64encode(image_data).decode('utf-8')

@app.route('/api/chat/<model_name>', methods=['POST'])
def chat(model_name: str):
    """Handle chat requests with optional image support"""
    try:
        prompt = request.form.get('prompt', '')
        image_file = request.files.get('image')
        
        # Prepare the payload
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": True
        }
        
        # Add image if provided
        if image_file:
            image_data = image_file.read()
            base64_image = encode_image_to_base64(image_data)
            payload["images"] = [base64_image]
        
        # Send request to Ollama
        response = requests.post(
            f"{OLLAMA_API_URL}/api/generate",
            json=payload,
            stream=True
        )
        
        def generate():
            for line in response.iter_lines():
                if line:
                    try:
                        json_response = json.loads(line)
                        if 'response' in json_response:
                            # Format as SSE
                            yield f"data: {json.dumps({'response': json_response['response']})}\n\n"
                    except json.JSONDecodeError:
                        continue
        
        return Response(generate(), mimetype='text/event-stream')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 