import numpy as np
import faiss, chromadb
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaEmbeddings
import os
from chromadb.config import Settings

#os.environ['CURL_CA_BUNDLE'] = ''

#---------------------------------------------------------------------------------------------------------------------- #
#                                               TODO                                                                    #                                                                      
#+++++++++++++++++++++++++++++++++++We have to experiment on Diffent Embedding Models+++++++++++++++++++++++++++++++++++#
#                                                                                                                       # 
#                           So some things to think about:                                                              #                                               
#                                                                                                                       #
#    Size of input - If you need to embed longer sequences, choose a model with a larger input capacity.                #
#    Size of embedding vector - Larger is generally a better representation but requires more compute/storage.          #
#    Size of model - Larger models generally result in better embeddings but require more compute power/time to run.    #
#    Open or closed - Open models allow you to run them on your own hardware whereas                                    #
#       closed models can be easier to setup but require an API call to get embeddings.                                 #
#                                                                                                                       #
#-----------------------------------------------------------------------------------------------------------------------#


class EmbeddingManager:
    """ Manage Emedding"""
    def __init__(self, chunks, embedding_model='bge-m3', base_url="http://ollama-container:11434"):
        self.chunks = chunks
        #self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.vectordb = None
        self.base_url = base_url
        self.embedding = OllamaEmbeddings(model=self.embedding_model, base_url=self.base_url)

    
    # Method to create embeddings
    def create_embeddings(self):

        # Creating an instance of OpenAIEmbeddings
        #embedding = HuggingFaceEmbeddings()
        #embedding = OllamaEmbeddings(model=self.embedding_model, base_url=self.base_url)

    
        # Creating an instance of Chroma with the sections and the embeddings
        self.vectordb = FAISS.from_documents(documents=self.chunks, embedding=self.embedding) # persist_directory=self.persist_directory)
        return self.vectordb



class FAISSEmbeddingManager:
    """Manage embeddings using FAISS."""
    def __init__(self, chunks, embedding_model='nomic-embed-text', base_url="http://ollama-container:11434"):
        self.chunks = chunks
        self.embedding_model = embedding_model
        self.base_url = base_url
        self.embedding = OllamaEmbeddings(model=self.embedding_model, base_url=self.base_url)  # Instantiate once
        self.faiss_index = None
        self.chunk_map = {}
        self.embedding_dimension = None

    def _get_embedding_dimension(self):
        """Retrieve the embedding dimension dynamically."""
        sample_text = "Test dimension"
        sample_vector = self.embedding.embed_query(sample_text)
        return len(sample_vector)

    def create_embeddings(self):
        self.embedding_dimension = self._get_embedding_dimension()
        #self.vectordb = faiss.GpuIndexFlatL2(self.embedding_dimension)
        gpu_resources = faiss.StandardGpuResources()
        #print(f"gpu_resources: {gpu_resources}")
        self.faiss_index = faiss.GpuIndexFlatL2(gpu_resources, self.embedding_dimension)

        for i, chunk in enumerate(self.chunks):
            vector = self.embedding.embed_documents([chunk.page_content])[0]
            self.faiss_index.add(np.array([vector], dtype=np.float32))
            self.chunk_map[i] = chunk

        return self.faiss_index

    def query_embeddings(self, query_text, top_k=5):
        """Retrieve top_k most similar document chunks for a query."""
        if self.faiss_index is None:
            raise ValueError("FAISS database not initialized. Call `create_embeddings` first.")

        query_vector = np.array([self.embedding.embed_query(query_text)], dtype=np.float32)
        
        distances, indices = self.faiss_index.search(query_vector, top_k)

        results = [(self.chunk_map[idx], distances[0][i]) for i, idx in enumerate(indices[0])]
        return results

# # ------------------------------------------------------------------------------------------#
# class FAISSEmbeddingManager:
#     def __init__(self, chunks=None, embedding_model='all-MiniLM-L6-v2'):
#         self.embedding_model = SentenceTransformer(embedding_model, device='cpu')
#         self.embeddings = None
#         self.index = None
#         self.chunks = chunks if chunks is not None else []

#     def embed_texts(self, texts=None):
#         """Embed the a list of texts and initialize the FAISS index.
#             If `texts` is None or Empty , use `self.chunks` instead.
#         """

#         if texts is None or not texts:
#             if not self.chunks:
#                 raise ValueError("No Texts provided for embedding.")
#             texts = [chunk.page_content for chunk in self.chunks]
#         else:
#             texts = [text.page_content for text in texts]

#         # Embed the texts
#         self.embeddings = self.embedding_model.encode(texts, batch_size=32, convert_to_tensor=True)
#         #embeddings_dict = dict(zip(texts, self.embeddings))

     
       
#         # Initialize the FAISS index
#         dimension = self.embeddings.shape[1]
#         self.index = faiss.IndexFlatL2(dimension)
#         self.index.add(np.array(self.embeddings))

#         return self.embeddings
    
#     def search(self, query, k=5):
#         """Search for the top k similar texts to a query."""

#         if self.index is None:
#             raise ValueError("FAISS index is not initialied. Please embed texts first")
#         # Embed the query
#         query_embedding = self.embedding_model.encode([query], batch_size=32, convert_to_tensor=True)

#         # Perform the search
#         distances, indices = self.index.search(np.array(query_embedding), k)
#         return distances, indices

#     def get_relevant_documents(self, query, k=5):
#         """Retrieve relevant documents for a given query using FAISS."""
#         distances, indices = self.search(query, k)
#         relevant_docs = [self.chunks[idx] for idx in indices[0]]
#         return relevant_docs

# class FAISSEmbeddingManager:
#     """Manage embeddings using FAISS."""
#     def __init__(self, chunks=None, embedding_model='all-MiniLM-L6-v2', use_sentence_transformer=False):
#         self.use_sentence_transformer = use_sentence_transformer
#         if use_sentence_transformer:
#             self.embedding_model = SentenceTransformer(embedding_model, device='cpu')  # For batch processing
#         else:
#             self.embedding_model = OllamaEmbeddings(model=embedding_model, base_url="http://ollama-container:11434")
        
#         self.chunks = chunks if chunks is not None else []
#         self.embeddings = None
#         self.index = None
#         self.chunk_map = {}

#     def embed_texts(self, texts=None):
#         """Embed texts and initialize FAISS index."""
#         if texts is None or not texts:
#             if not self.chunks:
#                 raise ValueError("No texts provided for embedding.")
#             texts = [chunk.page_content for chunk in self.chunks]

#         # Embed texts
#         if self.use_sentence_transformer:
#             self.embeddings = self.embedding_model.encode(texts, batch_size=32, convert_to_numpy=True)
#         else:
#             self.embeddings = np.array([self.embedding_model.embed_query(text) for text in texts])

#         # Initialize FAISS index
#         dimension = self.embeddings.shape[1]
#         self.index = faiss.IndexFlatL2(dimension)
#         self.index.add(self.embeddings)

#         # Create chunk map
#         self.chunk_map = {i: chunk for i, chunk in enumerate(self.chunks)}
#         return self.embeddings

#     def search(self, query, k=5):
#         """Search for the top `k` similar texts to a query."""
#         if self.index is None:
#             raise ValueError("FAISS index not initialized. Embed texts first.")

#         if self.use_sentence_transformer:
#             query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
#         else:
#             query_embedding = np.array([self.embedding_model.embed_query(query)])

#         # Perform the search
#         distances, indices = self.index.search(query_embedding, k)
#         return distances, indices

#     def get_relevant_documents(self, query, k=5):
#         """Retrieve relevant documents for a query using FAISS."""
#         distances, indices = self.search(query, k)
#         relevant_docs = [(self.chunk_map[idx], distances[0][i]) for i, idx in enumerate(indices[0])]
#         return relevant_docs