import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

def test_pdf_chain():
    # Initialize Ollama
    ollama = Ollama(base_url='http://localhost:11434', model="llama3.1")
    
    # Create a sample PDF file path (you'll need to provide your own PDF)
    pdf_path = "sample.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Please place a PDF file named '{pdf_path}' in the current directory")
        return
    
    try:
        # Load PDF
        print("Loading PDF...")
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        
        # Split text into chunks
        print("Splitting text into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        splits = text_splitter.split_documents(pages)
        
        # Create embeddings
        print("Creating embeddings...")
        embeddings = OllamaEmbeddings(base_url='http://localhost:11434', model="llama3.1")
        
        # Create vector store
        print("Creating vector store...")
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory="./chroma_db"
        )
        
        # Create a prompt template
        prompt_template = """Use the following pieces of context to answer the question at the end. 
        If you don't know the answer, just say that you don't know, don't try to make up an answer.

        Context: {context}

        Question: {question}
        Answer:"""
        
        PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )
        
        # Create the chain
        print("Creating QA chain...")
        chain = RetrievalQA.from_chain_type(
            llm=ollama,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(),
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )
        
        # Test the chain with a sample question
        print("\nTesting the chain with a sample question...")
        question = "What is this document about?"
        result = chain({"query": question})
        
        print("\nQuestion:", question)
        print("\nAnswer:", result["result"])
        print("\nSource Documents:")
        for doc in result["source_documents"]:
            print(f"- Page {doc.metadata.get('page', 'N/A')}: {doc.page_content[:100]}...")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    test_pdf_chain() 