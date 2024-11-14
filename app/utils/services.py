# app/utils/services.py
from app.utils.docu_manager import DocumentManager
from app.utils.embed_manager import EmbeddingManager

def initialize_app_state(app):
    document_manager = DocumentManager(directory_path="./app/Data")
    embedding_manager = EmbeddingManager(chunks=document_manager.split_document())
    vectordb = embedding_manager.create_embeddings()

    # Set up app state
    # print("Infos: intialize app states.")
    app.state.document_manager = document_manager
    app.state.embedding_manager = embedding_manager
    app.state.vectordb = vectordb