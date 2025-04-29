from flask import Flask, request, Response, jsonify, send_file
from flask_cors import CORS
import requests
import base64
import json
from typing import List, Dict
import os
from pathlib import Path
from .chat_manager import ChatManager

app = Flask(__name__)
CORS(app)

OLLAMA_API_URL = "http://localhost:11434"

# Initialize chat manager
chat_manager = ChatManager()

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

@app.route('/api/pdfs', methods=['GET'])
def get_pdfs():
    """Get list of all available PDFs"""
    return jsonify(chat_manager.get_available_pdfs())

@app.route('/api/pdfs/active', methods=['GET'])
def get_active_pdfs():
    """Get list of active PDFs in the current conversation"""
    return jsonify(chat_manager.get_active_pdfs())

@app.route('/api/pdfs/active', methods=['POST'])
def set_active_pdfs():
    """Set which PDFs to use for context"""
    try:
        pdf_hashes = request.json.get('pdf_hashes', [])
        chat_manager.set_active_pdfs(pdf_hashes)
        return jsonify({"message": "Active PDFs updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pdfs/preview/<pdf_hash>', methods=['GET'])
def get_pdf_preview(pdf_hash):
    """Get preview image for a PDF"""
    try:
        preview_path = chat_manager.pdf_manager.get_preview_image_path(pdf_hash)
        if preview_path and os.path.exists(preview_path):
            return send_file(preview_path)
        return jsonify({"error": "Preview not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/<model_name>', methods=['POST'])
def chat(model_name: str):
    """Handle chat requests with PDF context"""
    try:
        prompt = request.form.get('prompt', '')
        image_file = request.files.get('image')
        
        if image_file:
            # Handle image-based chat (existing vision model support)
            image_data = image_file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": True,
                "images": [base64_image]
            }
            
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
                                yield f"data: {json.dumps({'response': json_response['response']})}\n\n"
                        except json.JSONDecodeError:
                            continue
            
            return Response(generate(), mimetype='text/event-stream')
        else:
            # Handle text-based chat with PDF context
            response = chat_manager.chat(prompt)
            return jsonify({"response": response})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clear-chat', methods=['POST'])
def clear_chat():
    """Clear the chat history"""
    try:
        chat_manager.clear_chat()
        return jsonify({"message": "Chat history cleared successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 