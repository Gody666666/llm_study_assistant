import os
import json
from typing import List, Dict, Optional
from pathlib import Path
from langchain_community.llms import Ollama
from langchain.chains import ConversationalRetrievalChain, ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.schema import AIMessage, HumanMessage
from pdf_manager import PDFManager
import requests

class ChatManager:
    def __init__(self):
        self.llm = Ollama(base_url='http://localhost:11434', model="llama3.1")
        self.pdf_manager = PDFManager()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.chain = None
        self.active_pdfs: List[str] = []
        self._update_chain()
    
    def _update_chain(self):
        """Update the chain with current active PDFs"""
        # Define the prompt template
        template = """The following is a friendly conversation between a human and an AI.

Current conversation:
{chat_history}

In the conversation above, contents wrapped in HumanMessage are the user's previous messages.
Contents wrapped in AIMessage are the AI's previous responses. 
When you are responding to the user's message, you should use the same language as the user's message.
Directly give your reponse without any other text.

Human: {input}
AI:"""

        prompt = PromptTemplate(
            input_variables=["chat_history", "input"],
            template=template
        )

        if not self.active_pdfs:
            # Create a simple conversation chain without PDF context
            self.chain = ConversationChain(
                llm=self.llm,
                memory=self.memory,
                prompt=prompt,
                verbose=True
            )
            return
        
        # Get vector stores for active PDFs
        vector_stores = []
        for pdf_hash in self.active_pdfs:
            store = self.pdf_manager.get_vector_store(pdf_hash)
            if store:
                vector_stores.append(store)
        
        if not vector_stores:
            # Fall back to simple conversation chain if no valid vector stores
            self.chain = ConversationChain(
                llm=self.llm,
                memory=self.memory,
                prompt=prompt,
                verbose=True
            )
            return
        
        # Create a new chain with the combined vector stores
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=vector_stores[0].as_retriever(),  # Use first store for now
            memory=self.memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": prompt}
        )
    
    def set_active_pdfs(self, pdf_hashes: List[str]):
        """Set which PDFs to use for context"""
        self.active_pdfs = pdf_hashes
        self._update_chain()
    
    def get_active_pdfs(self) -> List[str]:
        """Get list of active PDFs"""
        return self.active_pdfs
    
    def get_available_pdfs(self) -> List[Dict]:
        """Get list of all available PDFs"""
        return self.pdf_manager.get_available_pdfs()
    
    def get_response(self, message: str, image_base64: Optional[str] = None) -> str:
        """Get a response from the model"""
        try:
            # Prepare the input for the model
            input_data = {"input": message}
            
            # If there's an image, add it to the input in the format Ollama expects
            if image_base64:
                # Ollama expects images in a specific format
                input_data = {
                    "model": self.llm.model,
                    "prompt": message,
                    "images": [image_base64],
                    "stream": False
                }
                
                # Make a direct request to Ollama's API for vision models
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json=input_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
                else:
                    return f"Error from Ollama API: {response.text}"
            
            # For non-vision requests, use the chain
            result = self.chain.invoke(input_data)
            
            # Extract the response content
            if isinstance(result, dict):
                response = result.get("response", "")
            elif isinstance(result, AIMessage):
                response = result.content
            elif isinstance(result, list) and len(result) > 0:
                # Handle list of messages
                response = result[0].content if hasattr(result[0], 'content') else str(result[0])
            else:
                response = str(result)
            
            if not response:
                return "I apologize, but I couldn't process your request. Please try again."
            
            return response
        except Exception as e:
            error_msg = f"Error getting response: {str(e)}"
            print(f"Chat error: {error_msg}")  # Add logging
            return error_msg
    
    def get_chat_history(self) -> List[Dict]:
        """Get the chat history"""
        return self.memory.chat_memory.messages
    
    def get_raw_messages(self) -> List[Dict]:
        """Get raw LangChain messages with their full structure"""
        messages = []
        for msg in self.memory.chat_memory.messages:
            messages.append({
                "type": msg.type,
                "content": msg.content,
                "additional_kwargs": msg.additional_kwargs
            })
        return messages
    
    def clear_chat_history(self):
        """Clear the chat history"""
        self.memory.clear()
        # Reinitialize the chain to ensure a fresh start
        self._update_chain() 