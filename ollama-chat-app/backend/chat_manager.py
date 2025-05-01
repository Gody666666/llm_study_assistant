import os
import json
from typing import List, Dict, Optional
from pathlib import Path
from langchain_community.llms import Ollama
from langchain.chains import ConversationalRetrievalChain, ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.schema import AIMessage, HumanMessage, BaseRetriever, Document
from pdf_manager import PDFManager
import requests
from langchain.retrievers import MultiVectorRetriever
from langchain.vectorstores import Chroma
from langchain.storage import InMemoryStore
from pydantic import BaseModel, Field

class MultiStoreRetriever(BaseRetriever):
    """Custom retriever that combines results from multiple vector stores"""
    
    vector_stores: List = Field(default_factory=list)
    docstore: InMemoryStore = Field(default_factory=InMemoryStore)
    
    def get_relevant_documents(self, query: str) -> List[Document]:
        """Get relevant documents from all vector stores"""
        all_docs = []
        seen_docs = set()  # To avoid duplicates
        
        for store in self.vector_stores:
            try:
                # Get relevant documents from each store
                docs = store.similarity_search(query, k=3)  # Get top 3 from each store
                for doc in docs:
                    # Use a unique identifier for each document
                    doc_id = f"{doc.metadata.get('source', '')}_{doc.page_content[:100]}"
                    if doc_id not in seen_docs:
                        seen_docs.add(doc_id)
                        all_docs.append(doc)
            except Exception as e:
                print(f"Error retrieving from store: {e}")
        
        return all_docs

    async def aget_relevant_documents(self, query: str) -> List[Document]:
        """Async version of get_relevant_documents"""
        return self.get_relevant_documents(query)

class ChatManager:
    def __init__(self):
        self.llm = Ollama(base_url='http://localhost:11434', model="llama3.1")
        self.pdf_manager = PDFManager()
        self.active_pdfs: List[str] = []
        self._update_chain()
    
    def _update_chain(self):
        """Update the chain with current active PDFs"""
        
        # Re-initialize memory each time the chain might change configuration
        # This ensures the memory's input/output keys match the chain type
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=True
        )

        # Define the base conversation template
        base_template = """The following is a friendly conversation between a human and an AI.

Current conversation:
{chat_history}

In the conversation above, contents wrapped in HumanMessage are the user's previous messages.
Contents wrapped in AIMessage are the AI's previous responses. 
When you are responding to the user's message, you should use the same language as the user's message.
Directly give your reponse without any other text.

Human: {input}
AI:"""

        # Define the retrieval template
        retrieval_template = """The following is a friendly conversation between a human and an AI.
Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

The user also provided a document for context (the user may call it a book, a chapter, or a section, or a pdf).
Here are the details of the provided document:
{context}

Current conversation:
{chat_history}

In the conversation above, contents wrapped in HumanMessage are the user's previous messages.
Contents wrapped in AIMessage are the AI's previous responses. 
When you are responding to the user's message, you should use the same language as the user's message.
Directly give your reponse without any other text.

Human: {question}
AI:"""

        if not self.active_pdfs:
            # Create a simple conversation chain without PDF context
            prompt = PromptTemplate(
                input_variables=["chat_history", "input"],
                template=base_template
            )
            # For ConversationChain, default memory keys might work, 
            # but we are re-initializing memory above anyway.
            # Ensure the input key matches the prompt's variable.
            self.memory.input_key = 'input' 
            # Chain's output key needs to be known or handled. Let's assume 'response' is default.
            # If ConversationChain outputs a different key, memory might need adjustment.
            self.chain = ConversationChain(
                llm=self.llm,
                memory=self.memory,
                prompt=prompt,
                verbose=True
            )
            return
        
        # --- Configuration for ConversationalRetrievalChain ---

        # Set the correct input and output keys for memory when using RetrievalQA
        self.memory.input_key = 'question'
        self.memory.output_key = 'answer' # Chain returns 'answer' as the main response key

        # Get vector stores for active PDFs
        vector_stores = []
        for pdf_hash in self.active_pdfs:
            store = self.pdf_manager.get_vector_store(pdf_hash)
            if store:
                vector_stores.append(store)
        
        if not vector_stores:
            # Fall back to simple conversation chain if no valid vector stores
            prompt = PromptTemplate(
                input_variables=["chat_history", "input"],
                template=base_template
            )
            self.chain = ConversationChain(
                llm=self.llm,
                memory=self.memory,
                prompt=prompt,
                verbose=True
            )
            return
        
        # Create a docstore to hold all documents
        docstore = InMemoryStore()
        
        # Create our custom retriever that combines results from all stores
        retriever = MultiStoreRetriever(vector_stores=vector_stores, docstore=docstore)
        
        # Load documents from each vector store into the docstore
        for store in vector_stores:
            try:
                # Get all documents from the store
                docs = store.get()
                if docs and len(docs) > 0:
                    # Store each document with a unique key
                    for i, doc in enumerate(docs):
                        docstore.mset([(f"{i}", doc)])  # Use simple index as key
            except Exception as e:
                print(f"Error loading documents from store: {e}")
        
        # Create a new chain with our custom retriever
        prompt = PromptTemplate(
            input_variables=["chat_history", "question", "context"],
            template=retrieval_template
        )
        
        # Configure the chain to properly use the context
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=self.memory, # Pass the correctly configured memory
            return_source_documents=True,
            combine_docs_chain_kwargs={
                "prompt": prompt,
                "document_prompt": PromptTemplate(
                    input_variables=["page_content"],
                    template="{page_content}"
                )
            },
            verbose=True
        )
    
    def set_active_pdfs(self, pdf_hashes: List[str]):
        """Set which PDFs to use for context"""
        print(f"Setting active PDFs: {pdf_hashes}")
        self.active_pdfs = pdf_hashes
        print(f"Active PDFs after setting: {self.active_pdfs}")
        self._update_chain()
        print(f"Active PDFs after chain update: {self.active_pdfs}")
    
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
            if isinstance(self.chain, ConversationalRetrievalChain):
                # For retrieval chain, we need to provide both input and question
                # The question will be used for retrieval, while input maintains conversation context
                input_data = {
                    "question": message
                }
            else:
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
            print(f"Result: {result}")

            # Extract the response content
            if isinstance(result, dict):
                # ConversationalRetrievalChain returns 'answer'
                response = result.get("answer") 
                if response is None:
                    # Fallback for other potential dict formats or if 'answer' is missing
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
        # Ensure memory object exists
        if hasattr(self, 'memory') and self.memory:
            return self.memory.chat_memory.messages
        return []
    
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
        # Create a new memory instance with default settings
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        # Reinitialize the chain, which will correctly configure memory in _update_chain
        self._update_chain() 