import numpy as np
#import faiss
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import os
os.environ['CURL_CA_BUNDLE'] = ''

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
    def __init__(self, chunks):
        self.chunks = chunks
        #self.persist_directory = persist_directory
        self.vectordb = None
        
    # Method to create embeddings
    def create_embeddings(self):

        # Creating an instance of OpenAIEmbeddings
        embedding = HuggingFaceEmbeddings()

        # Creating an instance of Chroma with the sections and the embeddings
        self.vectordb = FAISS.from_documents(documents=self.chunks, embedding=embedding) # persist_directory=self.persist_directory)
        return self.vectordb




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