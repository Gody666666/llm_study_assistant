# Study Assistant with LLM

This web application is an AI-driven study assistant built with Vue and Ollama, designed to enhance productivity and streamline the learning process. Leveraging a dedicated backend powered by LangChain, the app offers interaction with chat history management, image reading capabilities, and contextual understanding of PDF documents. We can also pre-process textbook PDFs and let the user to select specific chapters directly through the UI, allowing the backend to retrieve and provide relevant context to the language model.

![Screenshot](images/frontend_screenshot.png)

## Setup
Clone the repository and finish the following steps.

### Setup Ollama
Install Ollama and pull one or more large language models.

### Setup the frontend
Install frontend dependencies:
```bash
cd ollama-chat-app
npm install
```

### Setup the backend
```bash
cd ollama-chat-app/backend
pip install -r requirements.txt
```

## Run

### Start Ollama
```bash
ollama serve
```

### Start the backend server
```bash
cd ollama-chat-app/backend
python app.py
```

### Start the frontend development server
```bash
cd ollama-chat-app
npm run serve
```

Open your browser and navigate to `http://localhost:8080`

## Usage and Features

1. Select a model from the dropdown menu on the toolbar
2. If the selected model supports vision, you can upload an image
3. Enter your prompt in the text area and click "Send" or press Enter to send the prompt
4. Select textbook's chapters on the right to add context to the conversation

## System Design

### Application Design

![Screenshot](images/system.png)

TODO: Add description

### Preprocessing Textbooks

TODO: Add description