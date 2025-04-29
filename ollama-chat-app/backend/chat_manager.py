from typing import List, Dict, Optional
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from .pdf_manager import PDFManager

class ChatManager:
    def __init__(self):
        self.ollama = Ollama(base_url='http://localhost:11434', model="llama3.1")
        self.pdf_manager = PDFManager()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.active_pdfs: List[str] = []
        
        # Create a prompt template that includes both chat history and PDF context
        self.prompt_template = """Use the following pieces of context to answer the question at the end. 
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        Use the chat history to maintain context of the conversation.

        Chat History:
        {chat_history}

        Context from PDFs:
        {context}

        Question: {question}
        Answer:"""
        
        self.PROMPT = PromptTemplate(
            template=self.prompt_template,
            input_variables=["context", "question", "chat_history"]
        )
        
        self.chain = None
    
    def _create_chain(self):
        """Create or update the conversational chain with current PDF context"""
        # Get all active PDF vector stores
        vector_stores = [
            self.pdf_manager.get_vector_store(pdf_hash)
            for pdf_hash in self.active_pdfs
            if self.pdf_manager.get_vector_store(pdf_hash) is not None
        ]
        
        if not vector_stores:
            # If no PDFs are active, create a simple chain without retrieval
            self.chain = ConversationalRetrievalChain.from_llm(
                llm=self.ollama,
                memory=self.memory,
                chain_type="stuff",
                chain_type_kwargs={"prompt": self.PROMPT}
            )
        else:
            # Combine multiple vector stores into a single retriever
            from langchain.retrievers import MultiQueryRetriever
            retrievers = [store.as_retriever() for store in vector_stores]
            combined_retriever = MultiQueryRetriever.from_retrievers(retrievers)
            
            self.chain = ConversationalRetrievalChain.from_llm(
                llm=self.ollama,
                retriever=combined_retriever,
                memory=self.memory,
                chain_type="stuff",
                chain_type_kwargs={"prompt": self.PROMPT}
            )
    
    def set_active_pdfs(self, pdf_hashes: List[str]):
        """Set which PDFs to use for context"""
        # Validate PDFs exist
        valid_hashes = [
            pdf_hash for pdf_hash in pdf_hashes
            if self.pdf_manager.get_pdf_metadata(pdf_hash) is not None
        ]
        
        if valid_hashes != self.active_pdfs:
            self.active_pdfs = valid_hashes
            self._create_chain()
    
    def get_active_pdfs(self) -> List[Dict]:
        """Get list of active PDFs with their metadata"""
        return [
            self.pdf_manager.get_pdf_metadata(pdf_hash)
            for pdf_hash in self.active_pdfs
            if self.pdf_manager.get_pdf_metadata(pdf_hash) is not None
        ]
    
    def get_available_pdfs(self) -> List[Dict]:
        """Get list of all available PDFs"""
        return self.pdf_manager.get_available_pdfs()
    
    def chat(self, question: str) -> str:
        """Process a chat message with PDF context"""
        if self.chain is None:
            self._create_chain()
        
        result = self.chain({"question": question})
        return result["answer"]
    
    def clear_chat(self):
        """Clear the chat history"""
        self.memory.clear() 