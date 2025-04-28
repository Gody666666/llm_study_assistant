import requests
from pathlib import Path
import base64
import json

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def generate_vision_response(image_path):
    # Ollama API endpoint
    url = "http://localhost:11434/api/generate"
    
    # Encode the image
    base64_image = encode_image_to_base64(image_path)
    
    # Prepare the payload
    payload = {
        "model": "llama3.2-vision",
        "prompt": "What do you see in this image?",
        "stream": True,
        "images": [base64_image]
    }
    
    # Send request to Ollama with stream=True
    response = requests.post(url, json=payload, stream=True)
    
    # Process the streaming response
    for line in response.iter_lines():
        if line:
            try:
                json_response = json.loads(line)
                if 'response' in json_response:
                    # Print without newline to show streaming effect
                    print(json_response['response'], end='', flush=True)
                if json_response.get('done', False):
                    print()  # Add newline at the end
            except json.JSONDecodeError:
                print("Error decoding JSON response")

def main():
    # Replace with the path to your test image
    image_path = "test_image.jpg"
    
    if not Path(image_path).exists():
        print(f"Please ensure {image_path} exists in the current directory")
        return
    
    try:
        print("Sending image to Llama Vision model...")
        generate_vision_response(image_path)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
