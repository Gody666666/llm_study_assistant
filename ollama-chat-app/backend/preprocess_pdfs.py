import os
import json
import hashlib
import argparse
from typing import Dict, List
from pathlib import Path
from PyPDF2 import PdfReader
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

class PDFPreprocessor:
    def __init__(self, resources_dir: str = "../resources"):
        self.resources_dir = Path(resources_dir)
        self.embeddings = OllamaEmbeddings(base_url='http://localhost:11434', model="llama3.1")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
    def _get_pdf_hash(self, file_path: str) -> str:
        """Generate a unique hash for a PDF file"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _get_image_path(self, pdf_path: Path) -> str:
        """Get the path to the chapter image or book cover"""
        # First check for chapter image in the same directory
        chapter_image = pdf_path.parent / f"{pdf_path.stem}.png"
        if chapter_image.exists():
            return str(chapter_image.relative_to(self.resources_dir))
        
        # If no chapter image, use the book cover
        cover_image = pdf_path.parent / "cover.png"
        if cover_image.exists():
            return str(cover_image.relative_to(self.resources_dir))
        
        return None
    
    def _get_cover_path(self, book_dir: Path) -> str:
        """Get the path to the book cover image"""
        cover_image = book_dir / "cover.png"
        if cover_image.exists():
            return str(cover_image.relative_to(self.resources_dir))
        return None
    
    def _extract_metadata(self, pdf_path: str) -> Dict:
        """Extract metadata from PDF"""
        pdf_path = Path(pdf_path)
        reader = PdfReader(str(pdf_path))
        metadata = reader.metadata
        
        # Get the image path
        image_path = self._get_image_path(pdf_path)
        
        # Extract chapter number from filename (assuming format like "chapter1.pdf")
        chapter_num = 0
        try:
            chapter_num = int(pdf_path.stem.replace("chapter", ""))
        except ValueError:
            # If filename doesn't match the pattern, use 0
            pass
        
        return {
            "hash": self._get_pdf_hash(str(pdf_path)),
            "filename": pdf_path.name,
            "title": metadata.get("/Title", pdf_path.stem),
            "author": metadata.get("/Author", "Unknown"),
            "subject": metadata.get("/Subject", ""),
            "keywords": metadata.get("/Keywords", ""),
            "num_pages": len(reader.pages),
            "preview_image": image_path,
            "created_at": metadata.get("/CreationDate", ""),
            "modified_at": metadata.get("/ModDate", ""),
            "book_title": pdf_path.parent.name,
            "chapter": pdf_path.stem,
            "order": chapter_num
        }
    
    def _create_vector_store(self, pdf_path: str, pdf_hash: str):
        """Create and save vector store for a PDF"""
        store_dir = self.resources_dir / "vector_stores" / pdf_hash
        store_dir.mkdir(parents=True, exist_ok=True)
        
        # Load and process PDF
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        splits = self.text_splitter.split_documents(pages)
        
        # Create vector store
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=str(store_dir)
        )
        vectorstore.persist()
    
    def process_pdf(self, pdf_path: str, update_only: bool = False):
        """Process a single PDF file"""
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            print(f"File not found: {pdf_path}")
            return
        
        try:
            # Extract metadata
            metadata = self._extract_metadata(str(pdf_path))
            pdf_hash = metadata["hash"]
            
            # Create vector store only if not in update mode
            if not update_only:
                self._create_vector_store(str(pdf_path), pdf_hash)
            
            print(f"Successfully processed: {pdf_path}")
            return metadata
            
        except Exception as e:
            print(f"Error processing {pdf_path}: {str(e)}")
            return None
    
    def process_directory(self, pdf_dir: str, update_only: bool = False):
        """Process all PDFs in a directory"""
        pdf_dir = Path(pdf_dir)
        if not pdf_dir.exists():
            print(f"Directory not found: {pdf_dir}")
            return
        
        # Create necessary directories
        if not update_only:
            (self.resources_dir / "vector_stores").mkdir(exist_ok=True)
        
        # Process all PDFs and organize by textbook
        textbooks = {}
        for pdf_file in pdf_dir.glob("**/*.pdf"):
            metadata = self.process_pdf(str(pdf_file), update_only)
            if metadata:
                book_title = metadata["book_title"]
                if book_title not in textbooks:
                    book_dir = pdf_file.parent
                    textbooks[book_title] = {
                        "title": book_title,
                        "cover_image": self._get_cover_path(book_dir),
                        "chapters": []
                    }
                textbooks[book_title]["chapters"].append(metadata)
        
        # Sort chapters by order
        for book in textbooks.values():
            book["chapters"].sort(key=lambda x: x["order"])
        
        return textbooks
    
    def generate_index(self, textbooks: Dict):
        """Generate an index of all processed PDFs"""
        # Save index
        index_file = self.resources_dir / "pdf_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(textbooks, f, indent=2, ensure_ascii=False)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process PDFs and generate metadata/vector stores')
    parser.add_argument('--update-only', action='store_true', help='Update metadata without rebuilding vector stores')
    args = parser.parse_args()
    
    # Get the absolute path to the resources directory
    current_dir = Path(__file__).parent
    resources_dir = current_dir.parent / "resources"
    
    preprocessor = PDFPreprocessor(str(resources_dir))
    
    # Process PDFs in the textbook directory
    textbooks_dir = resources_dir / "textbook"
    if textbooks_dir.exists():
        print("Processing PDFs in textbook directory...")
        textbooks = preprocessor.process_directory(str(textbooks_dir), args.update_only)
        
        # Generate index
        print("Generating PDF index...")
        preprocessor.generate_index(textbooks)
    else:
        print(f"Textbook directory not found at: {textbooks_dir}")

if __name__ == "__main__":
    main() 