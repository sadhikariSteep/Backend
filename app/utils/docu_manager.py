import glob, os
import uuid
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, PyMuPDFLoader, PDFPlumberLoader, PDFMinerLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path
import PyPDF2
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore

from app.database.config import get_db
from app.database.docstore import PostgresStore
from typing import Iterable, List, Optional, Any
#-------------------------------------------------------------------------------#
#                           TODO                                                #
# conversion from diffent document format like docx, pdf, which contain...      #
# so that please check the converted pain text contain txt in their oder        # 
#                                                                               #
#                                                                               #
#-------------------------------------------------------------------------------#

class DocumentManager:
    """ Load the document from user defined location and split it into smaller chunks so that it can easily process"""
    def __init__(self, directory_path, glob_pattern=['**/*.pdf', '**/*.docx', '**/*.txt']):
        self.directory_path = directory_path
        self.glob_pattern = glob_pattern
        self.documents = []  # Raw loaded documents
        self.chunks = [] # Processed chunks

    def load_documents(self):
        """ Load the documents form the list of file path."""

        for pattern in self.glob_pattern:
            # Get all documents matching the pattern, including subdirectories
            documents_path = glob.glob(os.path.join(self.directory_path, pattern), recursive=True)
            #documents_path = glob.glob(f"{self.directory_path}/**/*", recursive=True)
            # print("list of given documents", documents_path)
            for document_path in documents_path:
                # Load PDF if it matches
                if document_path.endswith('.pdf'):
                    # Replace this with actual PDF loading code
                    #print("pdf loader", document_path)
                    document_loader = PyMuPDFLoader(document_path)#, extract_images=True)
                # Check for docx and load it
                elif document_path.endswith('.docx'):
                    document_loader = Docx2txtLoader(document_path)
                # Check for txt and load it
                elif document_path.endswith('.txt'):
                    document_loader = TextLoader(document_path)
                #other cases asked user to check the document format.
                else:
                    print(f'Please check documets format.')

                # Extend the documents list with loaded content
                self.documents.extend(document_loader.load())

        return self.documents
    # -----------------------
    # Step 2: Split Documents simple methods
    # -----------------------
    def split_document(self, documents=None):
        """Split a list of documents into Chunks."""
        if documents is None:
            # Load the documents if they havenot been loaded yet
            if not self.documents:
                self.load_documents()
            # Load the document where they saved
            documents = self.documents
        # Check documents
        if not documents:
            raise ValueError("No documents to split. Please check the documents first.")
        
        # split mehtod
        # we can test here other splitter
        text_splitter = RecursiveCharacterTextSplitter(
                            chunk_size=2500,
                            chunk_overlap=200,
                            length_function=len,
                            is_separator_regex=False,

                            )
        self.chunks = text_splitter.split_documents(documents)
        return self.chunks


class AdvancedDocumentManager:
    """Manages document loading, splitting, and retriever creation with clear separation of steps."""
        
    def __init__(self, directory_path, glob_pattern=['**/*.pdf', '**/*.docx', '**/*.txt']):
        self.directory_path = directory_path
        self.glob_pattern = glob_pattern
        self.documents = []
        self.combined_text = []
        self.metadata = []
        

    def load_documents(self):
        """ Load the documents form the list of file path."""

        self.documents.clear()
        documents_path = glob.glob(f"{self.directory_path}/**/*", recursive=True)
        print("list of given documents", documents_path)
        for document_path in documents_path:
            # Load PDF if it matches
            if document_path.endswith('.pdf'):
                print(f"Loading PDF file: {document_path}")
                #document_loader = PyMuPDFLoader(file_path=document_path)#, concatenate_pages=True)#, extract_images=True)PDFPlumberLoader
                #document = document_loader.load()
                #self.documents.extend(document)
                full_text  = self.extract_text_with_formating(document_path)
                if full_text :
                    self.documents.append(Document(page_content=full_text , metadata={'source': document_path,"doc_id": str(uuid.uuid4())}))
                
        return self.documents
    
    def extract_text_with_formating(self, pdf_path):
        """Extract text from a PDF file using PDFMiner."""
        content = ""
        try: 
            with open(pdf_path, 'rb') as file:
                # Open the PDF file
                reader = PyPDF2.PdfReader(file)
                # Extract text from each page
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        content += f"\n---------- New Page Started (Page No.: {page_num + 1}) ----------\n{text}\n"

        except Exception as e:
            print(f"Error extracting text: {e}")

        return content
            
    # -----------------------
    # Step 2: Split Documents
    # -----------------------
    def split_document(self, documents=None):
        """Split a list of documents into Chunks."""
        if documents is None:
            # Load the documents if they havenot been loaded yet
            if not self.documents:
                 self.load_documents()
            # # Load the document where they saved
            documents = self.documents
            print(f"Total number of documents: {len(documents)}")
        # Check documents
        if not documents:
            raise ValueError("No documents to split. Please check the documents first.")
        
        # split mehtod
        # we can test here other splitter
        text_splitter = RecursiveCharacterTextSplitter(
                            chunk_size=3000,
                            chunk_overlap=200

                            )
        self.chunks = text_splitter.split_documents(documents)
        return self.chunks          
    
    def monkeypatch_FAISS(self, embeddings_model):
        def _add_texts(self, texts, metadatas=None, ids=None, **kwargs):
            embeddings = embeddings_model.embed_documents(texts)
            return self._FAISS__add(texts, embeddings, metadatas=metadatas, ids=ids)
        FAISS.add_texts = _add_texts

    # -------------------------------
    # Step 3: Create Retriever(s)
    # -------------------------------
    def create_parent_retriever(self, use_postgres: bool = False, emd_model:str='nomic-embed-text'):
        """Create retriever directly from raw documents"""
        embedding = OllamaEmbeddings(model=emd_model, base_url="http://ollama-container:11434")

        # Load the documents if they havenot been loaded yet
        if not self.documents:
            self.load_documents()
        
        texts = ["FAISS is an important library", "LangChain supports FAISS"]
        self.monkeypatch_FAISS(embedding)
        vectordb = FAISS.from_texts(texts, embedding)
        if use_postgres:
            # PostgreSQL version
            store = PostgresStore(db=next(get_db()))  # Get database session
            store._ensure_clean_state()
        else:
            # In-memory version
            store = InMemoryStore()
            
        parent_splitter = RecursiveCharacterTextSplitter(chunk_size=3000)
        child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, add_start_index=True)
        
        retriever = ParentDocumentRetriever(
                            vectorstore=vectordb,
                            docstore=store,
                            id_key="parent_id",
                            parent_splitter=parent_splitter, 
                            child_splitter=child_splitter,
                            child_metadata_fields=["source"],)
        retriever.add_documents(self.documents)

        return retriever