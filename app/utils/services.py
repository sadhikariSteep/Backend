# app/utils/services.py
from fastapi import logger
from app.utils.docu_manager import AdvancedDocumentManager, DocumentManager
from app.utils.embed_manager import EmbeddingManager, FAISSEmbeddingManager


from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from queue import Queue
import threading

class FileChangeHandler(FileSystemEventHandler):
    """
        Watches for file changes (creation, modification, deletion) in a directory and and queues events.
    """
    def __init__(self, app, queue):
        """
        Initialize the handler with a reference to the FastAPI app and a shared queue.
        
        :param app: The FastAPI app instance.
        """
        self.app = app
        # self.queue = queue

    def on_created(self, event):
        """
        Triggered when a file is created in the watched directory.
        :param event: File system event object.
        """
        if not event.is_directory:
            print(f"File created: {event.src_path}")
            self.process_file(event.src_path, action="created")
    
    def on_deleted(self, event):
        """
        Triggered when a file is deleted in the watched directory.
        :param event: File system event object.
        """

        if not event.is_directory:
            print(f"File deleted: {event.src_path}")
            self.process_file(event.src_path, action="deleted")

    def on_modified(self, event):
        """
        Triggered when a file is modified in the watched directory.
        
        :param event: File system event object.
        """
        if not event.is_directory:  # Ignore directory modifications
            print(f"File modified: {event.src_path}")
            self.process_file(event.src_path, action="modified")


    def process_file(self, file_path, action):

        """
        Process file changes and update vector database.
        """
        
        document_manager = self.app.state.document_manager
        embedding_manager = self.app.state.embedding_manager
        vectordb = self.app.state.vectordb
        
        if action=="created":
            print(f"Processing new file: {file_path}")
            # Recreate embeddings for all files (or just the new one,based on design)
            chunks = document_manager.split_document([file_path])
            embedding_manager.add_to_vectordb(chunks, vectordb)


        elif action=="deleted":
            print(f"Removing file: {file_path}")
            # Handle file deletion
            # Remove embeddings for the deleted file

            file_name = file_path.split("/")[-1]
            vectordb = self.app.state.vectordb
            if vectordb:
                vectordb.remove_embeddings(file_name)
          





def start_file_watcher(app):
    """
    Initialize the file watcher and event processor.

    :param app: The FastAPI app instance.
    """

    # Initialize app state if not already initialized
    if not hasattr(app.state, "document_manager"):
        initialize_app_state(app)

    handler = FileChangeHandler(app)
    observer = Observer()
    observer.schedule(handler, path="app/files/", recursive=False)
    observer.start()

    # Start file processor in a separate thread
    #threading.Thread(target=process_file, args=(app, queue), daemon=True).start()

async def initialize_app_state(app):
    try: 
        document_manager = AdvancedDocumentManager(directory_path = "app/files/")#DocumentManager(directory_path = "app/files/")
        embedding_manager = EmbeddingManager(chunks=document_manager.split_document())
        vectordb = embedding_manager.create_embeddings()
        document_manager.load_documents()
        retriever = document_manager.create_parent_retriever(use_postgres=True, emd_model='bge-m3')
        #embedding_manager = FAISSEmbeddingManager(chunks=document_manager.split_document())
        #vectordb = embedding_manager.create_embeddings()
        #print("Infos: vectordb created.", vectordb)

        # Set up app state
        app.state.document_manager = document_manager
        app.state.embedding_manager = embedding_manager
        app.state.vectordb = vectordb
        app.state.retriever = retriever
        logger.info("App state initialized successfully.")

    except Exception as e:
        logger.error(f"Error initializing app state {e}", exe_info =True)
        raise