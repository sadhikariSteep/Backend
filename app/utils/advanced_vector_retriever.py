from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from app.utils.docu_manager import AdvancedDocumentManager

class AdvancedVectorRetriever:
    def __init__(self, top_k=5):
        """
        Initialize the AdvancedVectorRetriever.

        Args:
            vector_database: The vector database instance to query.
            top_k (int): Number of top results to return. Default is 5.
            
        """
        #self.vectordb = vectordb
        self.top_k = top_k
        document_manager = AdvancedDocumentManager(directory_path = "app/files/")#DocumentManager(directory_path = "app/files/")

        document_manager.load_documents()
        self.parent_retriever = document_manager.create_parent_retriever(use_postgres=True, emd_model='bge-m3')
        #self.documents = AdvancedDocumentManager.create_parent_retriever(use_postgres=True)

    def retrieve_documents(self, query):#search_type="similarity"):
        """
        Retrieve documents from the vector database based on the configured strategy.
        search_type (str): The strategy to use for retrieval (e.g., "similarity").
 
        Returns:
            A list of retrieved documents.
        """
        # Implement default search logic here
        #return self.vectordb.as_retriever(search_type=search_type, search_kwargs={"k": self.top_k})
        #parent_retriever=self.parent_retriever.as_retriever(search_kwargs={"k": self.top_k})

        return self.parent_retriever.invoke(query)

    def hybrid_search(self, query, weights=None, chunks=None):
        """
        Perform a hybrid search combining multiple retrieval strategies.

        Args:
            query (str): The input query to search for.
            weights (dict): Weights for different retrieval strategies 
                            (e.g., {"text": 0.7, "embedding": 0.3}).

        Returns:
            A list of hybrid search results.
        """
        if weights is None:
            weights = [0.5, 0.5]
        # Implement advanced search logic here
        parent_docs = self.retrieve_documents(query)
        keyword_retriever = BM25Retriever.from_documents(parent_docs, search_type={"k":self.top_k})

        ensemble_retriever = EnsembleRetriever(retrievers=[self.parent_retriever, keyword_retriever], weights=weights)  
        compressed_docs = ensemble_retriever.invoke(query)
        return compressed_docs