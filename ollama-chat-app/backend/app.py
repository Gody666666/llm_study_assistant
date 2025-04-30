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

# Store selected chapters per book
selected_chapters = {}

# Get the absolute path to the resources directory
current_dir = Path(__file__).parent
resources_dir = current_dir.parent / "resources"

def get_available_models() -> List[Dict]:
    """Get list of available models from Ollama"""
    try:
        # Get list of models
        response = requests.get(f"{OLLAMA_API_URL}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            available_models = []
            
            for model in models:
                # Check if model name contains vision-related keywords
                model_name = model["name"].lower()
                supports_vision = any(keyword in model_name for keyword in ["vision", "llava", "bakllava"])
                
                available_models.append({
                    "name": model["name"],
                    "supportsVision": supports_vision
                })
            
            return available_models
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

@app.route('/api/pdf/active', methods=['POST'])
def set_active_pdfs():
    """Set which PDFs to use for context"""
    try:
        data = request.get_json()
        pdf_hashes = data.get('pdf_hashes', [])
        book_title = data.get('book_title', '')
        
        print(f"Received PDF hashes: {pdf_hashes}")
        print(f"Book title: {book_title}")
        
        # Store selected chapters for the book
        if book_title:
            selected_chapters[book_title] = pdf_hashes
            print(f"Stored chapters for {book_title}: {selected_chapters[book_title]}")
        
        # Update active PDFs in chat manager with the actual PDF hashes
        chat_manager.set_active_pdfs(pdf_hashes)
        return jsonify({"message": "Active PDFs updated successfully"})
    except Exception as e:
        print(f"Error in set_active_pdfs: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/pdf/active/<book_title>', methods=['GET'])
def get_active_chapters(book_title: str):
    """Get active chapters for a specific book"""
    try:
        chapters = selected_chapters.get(book_title, [])
        return jsonify({"chapters": chapters})
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
            image = None
        else:
            message = request.form.get('message') or request.form.get('prompt')
            image_file = request.files.get('image')
            image = image_file.read() if image_file else None
        
        if not message and not image:
            return jsonify({"error": "No message or image provided"}), 400
        
        def generate():
            try:
                # Convert image to base64 if present
                image_base64 = None
                if image:
                    image_base64 = base64.b64encode(image).decode('utf-8')
                
                # Update the model if specified
                if model_name:
                    chat_manager.llm.model = model_name
                
                response = chat_manager.get_response(message, image_base64)
                if not response:
                    yield f"data: {json.dumps({'error': 'No response from model'})}\n\n"
                else:
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

@app.route('/api/pdf/hash/<path:filename>')
def get_pdf_hash(filename: str):
    """Get the hash of a PDF file"""
    try:
        pdf_hash = pdf_manager.get_pdf_hash(filename)
        return jsonify({"hash": pdf_hash})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 