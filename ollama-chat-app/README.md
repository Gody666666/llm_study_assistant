# Ollama Chat Application

A Vue.js application with TypeScript and Vuetify that provides a chat interface for Ollama models, including support for vision models.

## Features

- Model selection from available Ollama models
- Support for vision models with image upload
- Streaming responses
- Modern UI with Vuetify
- TypeScript support
- Flask backend with CORS support

## Prerequisites

- Node.js (v14 or higher)
- Python 3.8 or higher
- Ollama installed and running locally
- npm or yarn package manager

## Setup

1. Clone the repository
2. Install frontend dependencies:
   ```bash
   cd ollama-chat-app
   npm install
   ```

3. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. Start the backend server:
   ```bash
   cd backend
   python app.py
   ```

5. In a new terminal, start the frontend development server:
   ```bash
   cd ollama-chat-app
   npm run serve
   ```

6. Open your browser and navigate to `http://localhost:8080`

## Usage

1. Select a model from the dropdown menu
2. If the selected model supports vision, you can upload an image
3. Enter your prompt in the text area
4. Click "Send" or press Enter to send the prompt
5. The response will stream in real-time

## Development

- Frontend: Vue 3 with TypeScript and Vuetify
- Backend: Flask with CORS support
- API: Ollama API integration

## License

MIT 