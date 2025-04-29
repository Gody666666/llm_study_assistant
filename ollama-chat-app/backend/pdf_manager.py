import os
import json
import hashlib
from typing import List, Dict, Optional
from pathlib import Path
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

class PDFManager:
    def __init__(self, resources_dir: str = "../resources"):
        self.resources_dir = Path(resources_dir)
        self.embeddings = OllamaEmbeddings(base_url='http://localhost:11434', model="llama3.1")
        self.vector_stores: Dict[str, Chroma] = {}
        self.textbooks: Dict[str, Dict] = {}
        self.available_pdfs: Dict[str, Dict] = {}
        self._load_pdf_index()
        
    def _load_pdf_index(self):
        """Load the PDF index and available PDFs"""
        index_file = self.resources_dir / "pdf_index.json"
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                self.textbooks = json.load(f)
                # Create a flat list of all PDFs for easy access
                for textbook in self.textbooks.values():
                    for chapter in textbook["chapters"]:
                        self.available_pdfs[chapter["hash"]] = chapter
    
    def get_available_pdfs(self) -> List[Dict]:
        """Get list of all available PDFs"""
        return list(self.available_pdfs.values())
    
    def get_pdf_metadata(self, pdf_hash: str) -> Optional[Dict]:
        """Get metadata for a specific PDF"""
        return self.available_pdfs.get(pdf_hash)
    
    def get_vector_store(self, pdf_hash: str) -> Optional[Chroma]:
        """Get the vector store for a specific PDF"""
        if pdf_hash not in self.vector_stores:
            store_dir = self.resources_dir / "vector_stores" / pdf_hash
            if store_dir.exists():
                self.vector_stores[pdf_hash] = Chroma(
                    persist_directory=str(store_dir),
                    embedding_function=self.embeddings
                )
        return self.vector_stores.get(pdf_hash)
    
    def get_preview_image_path(self, pdf_hash: str) -> Optional[str]:
        """Get the preview image path for a PDF"""
        metadata = self.get_pdf_metadata(pdf_hash)
        if metadata and "preview_image" in metadata:
            return str(self.resources_dir / metadata["preview_image"])
        return None 