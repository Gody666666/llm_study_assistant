from flask import Flask, request, Response, jsonify, send_file, send_from_directory
from flask_cors import CORS
import requests
import base64
import json
from typing import List, Dict
import os
from pathlib import Path
from chat_manager import ChatManager
from pdf_manager import PDFManager

app = Flask(__name__)
CORS(app)

OLLAMA_API_URL = "http://localhost:11434"

# Initialize managers
chat_manager = ChatManager()
pdf_manager = PDFManager()

# Get the absolute path to the resources directory
current_dir = Path(__file__).parent
resources_dir = current_dir.parent / "resources"

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

@app.route('/api/chat', methods=['POST'])
@app.route('/api/chat/<model_name>', methods=['POST'])
def chat(model_name: str = None):
    """Handle chat requests with optional model specification"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            message = data.get('message') or data.get('prompt')
        else:
            message = request.form.get('message') or request.form.get('prompt')
        
        if not message:
            return jsonify({"error": "No message or prompt provided"}), 400
        
        def generate():
            try:
                response = chat_manager.get_response(message)
                yield f"data: {json.dumps({'response': response})}\n\n"
            except Exception as e:
                print(f"Chat error: {str(e)}")  # Add logging
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(generate(), mimetype='text/event-stream')
    except Exception as e:
        print(f"Chat error: {str(e)}")  # Add logging
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    try:
        history = chat_manager.get_chat_history()
        return jsonify({"history": history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/raw-messages', methods=['GET'])
def get_raw_messages():
    """Get raw LangChain messages"""
    try:
        messages = chat_manager.get_raw_messages()
        return jsonify({"messages": messages})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/history', methods=['DELETE'])
def clear_chat_history():
    """Clear the chat history"""
    try:
        chat_manager.clear_chat_history()
        return jsonify({
            "message": "Chat history cleared successfully",
            "status": "success"
        })
    except Exception as e:
        print(f"Error clearing chat history: {str(e)}")  # Add logging
        return jsonify({
            "error": "Failed to clear chat history",
            "details": str(e)
        }), 500

@app.route('/api/pdf/index', methods=['GET'])
def get_pdf_index():
    """Get the PDF index file"""
    try:
        index_file = resources_dir / "pdf_index.json"
        if not index_file.exists():
            return jsonify({"error": "PDF index not found"}), 404
        
        with open(index_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        return jsonify(index_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/pdf/<path:filename>')
def get_pdf(filename):
    """Serve PDF files from the resources directory"""
    try:
        return send_from_directory(resources_dir, filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route('/api/pdf/preview/<path:filename>')
def get_pdf_preview(filename):
    """Serve PDF preview images from the resources directory"""
    try:
        return send_from_directory(resources_dir, filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000) 