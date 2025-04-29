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
        template = """The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context.

Current conversation:
{chat_history}

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
    
    def get_response(self, message: str) -> str:
        """Get a response from the model"""
        try:
            # Get response from the chain using invoke
            result = self.chain.invoke({"input": message})
            
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