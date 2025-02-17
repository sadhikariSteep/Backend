# app/utils/dependencies.py
from fastapi import Depends, Request

def get_document_manager(request: Request):
    return request.app.state.document_manager

def get_embedding_manager(request: Request):
    return request.app.state.embedding_manager

def get_vectordb(request: Request):
    return request.app.state.vectordb

def get_retriever(request: Request):
    if not hasattr(request.app.state, "retriever"):
        raise RuntimeError("Retriever not initialzed. App state might bot be set up.")

    return request.app.state.retriever