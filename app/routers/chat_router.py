# app/routers/chat.py
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from app.database.docstore import PostgresStore
from app.database.helper_insert_update_chathistory import clear_all_chat_history, delete_chat_history_by_session, fetch_all_histories_grouped_by_session, fetch_chat_history_for_each_session, insert_user_question, update_assistant_answer
from app.routers.helper import parse_markdown_to_blocks
from app.routers.user_router import get_user_id_from_token
from app.schemas.chat_schema import ChatCreate, ChatResponse, ChatRequest, ContentBlock
from app.database.config import get_db
from langchain_ollama import OllamaLLM
from app.utils.chain_manager import *
from app.utils.docu_manager import *
from app.utils.embed_manager import *
from app.utils.dependencies import *
from app.utils.faiss_chroma_manager import *
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler
#document_manager = DocumentManager(directory_path="app/Data")
#document_manager = AdvancedDocumentManager(directory_path="app/Data")
embedding_manager = None
conversation_chain_manager = None


router = APIRouter(
    prefix="/bot",
    tags=["bot"],
)


@router.get("/")
async def root():
  return { "message": "Hello Chat." }


@router.get("/documents")
def get_documents():
    document_manager = DocumentManager(directory_path = "app/files/")
    chunks = document_manager.split_document()
    embedding_manager = EmbeddingManager(chunks=chunks)
    vectordb = embedding_manager.create_embeddings()
    return vectordb
def get_embedding_model(model_name: str):
    llama = OllamaEmbeddings(model=model_name, base_url='http://ollama-container:11434')
    return llama
def get_model(model_name: str):
    llama = OllamaLLM(model=model_name, base_url='http://ollama-container:11434')
    return llama
def get_parent_doc_retriever():
    document_manager = AdvancedDocumentManager(directory_path = "app/files/")
    document = document_manager.load_documents()

    chunks = document_manager.split_document()
    return chunks, document

@router.post("/faiss")
async def chat_with_faiss(request: ChatRequest):

    document_manager = DocumentManager(directory_path = "app/files/")
    embedding_manager_faiss = FAISSEmbeddingManager(chunks=document_manager.split_document())
    faiss_index = embedding_manager_faiss.create_embeddings()
    context = embedding_manager_faiss.query_embeddings(query_text=request.question, top_k=5)
    print(context)
    context = "\n".join([f"Document {i+1}: {chunk.page_content}" for i, (chunk, _) in enumerate(context)])

    llm = OllamaLLM(model="llama3.1:8b", base_url='http://ollama-container:11434')

    prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are an intelligent assistant for answer questions related tasks.\
        Use the following pieces of retrieved context to answer the quesion.\
        Your responses should be based solely on the provided company data, ensuring accuracy and relevance. \
        Use the most appropriate and relevant data from the repository to generate clear, concise, and factual answers to user queries.\
        Always search for anything requested in the query within the documents or database and provide the best possible response based on the retrieved data.\
        Make sure your answer is relevent to the quesion and it is answered from the context only.\
        Answer only in German "
     "Question: {question}\n\nContext: {context}"
    ),
    ("user", "{question}")
])

    chain = (
    RunnablePassthrough()
    | prompt
    | llm
    | StrOutputParser()
)
    response = chain.invoke({"question": request.question, "context": context})

    # Print the generated response
    print("response from llm hey ", response)
    return {"response": response}


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    session_id: Optional[str] = Header(None),  # Extract 'Session-ID' from headers
):
    """
    Streaming response API for real-time chatbot interactions.
    """
    # Step 1: Capture question time
    query_time = datetime.now()
    print("Processing query with model:", request.selectedModel)
    document_manager = DocumentManager(directory_path = "app/files/")
    embedding_manager = EmbeddingManager(chunks=document_manager.split_document())
    vectordb = embedding_manager.create_embeddings()

    # Step 2: Retrieve relevant documents
    retriever = AdvancedVectorRetriever(vectordb)
    retriever_vanilla = retriever.retrieve_documents(search_type="similarity")

    # Step 3: Initialize conversational manager
    conversational_manager = ConversationalChainManager(llm_name=request.selectedModel)
    chain = conversational_manager.build_conversation_chain(retriever_vanilla)

    # Step 4: Create an async generator for streaming
    async def response_generator():
        callback = AsyncIteratorCallbackHandler()
        # Directly using the `astream` function to stream the tokens
        async for token in chain.astream(
            {"input": request.question},
            config={"configurable": {"session_id": session_id}, "callbacks": [callback]},
        ):
            # Check if 'answer' exists and is a string
            if "answer" in token and isinstance(token["answer"], str):
                yield token["answer"]
            #else:
                #logging.warning(f"Unexpected token format: {token}")

    # Step 5: Return a streaming response
    return StreamingResponse(response_generator(), media_type="text/event-stream")
    
@router.post("/query", response_model=ChatResponse)
async def chat_with_bot(
    request: ChatRequest, 
    #vectordb=Depends(get_vectordb), 
    #embedding_manager=Depends(get_embedding_manager),
    retriever=Depends(get_retriever),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_user_id_from_token),
    session_id: Optional[str] = Header(None),  # Extracts 'Session-ID' from headers
    ):
         # Step 1: Capture the question time (user query time)
        query_time = datetime.now()
        chat_id = insert_user_question(session_id, user_id, request.question, query_time, db=db)
        #print("going inside the fucntion conversation manager", request.selectedModel)
        # Step 2: Process user query

        #document_manager = AdvancedDocumentManager(directory_path = "app/files/")
        #document_manager.load_documents()
        #retriever = AdvancedVectorRetriever(vectordb)
        #retriever = document_manager.create_parent_retriever(use_postgres=True, emd_model='bge-m3')
        #retriever_vanilla = retriever.retrieve_documents(search_type="similarity")
        #retriever_mmr = retriever.retrieve_documents(search_type="mmr")

        conversational_manager = ConversationalChainManager(llm_name= request.selectedModel)#'deepseek-r1:32b')
        conversational_manager.build_conversation_chain(retriever)
        ans = conversational_manager.process_user_query(session_id=session_id, user_query=request.question)
        #print('type of ans',type(ans))
        print("ans: ", ans)

        response_time = datetime.now()
        parsed_blocks = parse_markdown_to_blocks(ans)
       
        duration = (response_time - query_time).total_seconds()
        print("time taken for processing...", duration)

        # Add the duration as a "think" block
        duration_block = ContentBlock(type="botStatusMsg", content=f"Thought for {duration:.1f} seconds")
        parsed_blocks.append(duration_block)
        update_assistant_answer(chat_id, parsed_blocks, response_time, db=db)
        #return {"response": ans}
        print ("after parcing: ", parsed_blocks)
        return ChatResponse(response=parsed_blocks,)
                            # duration=duration
                            #timestamp_query = query_time.isoformat(),  # Send the query timestamp
                            #timestamp_response = response_time.isoformat())

@router.post("/query_simple")
async def chat_with_bot_simple(
    request: ChatRequest,
    session_id: Optional[str] = Header(None),
    search_type: str= "similarity"  # Extracts 'Session-ID' from headers  
):
    # Initialize DocumentManager and retrieve chunks
    document_manager = DocumentManager(directory_path="app/files/")
    chunks = document_manager.split_document()

    # Create embeddings using EmbeddingManager
    embedding_manager = EmbeddingManager(chunks=chunks)
    vectordb = embedding_manager.create_embeddings()

    # Initialize retriever with vector database
    retriever_doc = AdvancedVectorRetriever(vectordb)
    retriever = retriever_doc.retrieve_documents(search_type=search_type)
    
    # Initialize ConversationalChainManager
    conversational_manager = ConversationalChainManager()
    
    # Build conversation chain for vanilla retriever
    chain = conversational_manager.build_conversation_chain(retriever)
    response = chain.invoke(
            {"input": request.question},
            config={"configurable": {"session_id": session_id}}
            )

    
    # Return responses for both retrieval methods
    return {
        "response": response["answer"]
    }

@router.get("/history", response_model=dict)
def get_all_chat_histories(db: Session = Depends(get_db)):
    return fetch_all_histories_grouped_by_session(db)

@router.get("/history/{session_id}", response_model=dict)
def get_chat_histories_by_session(session_id: str, db: Session = Depends(get_db)):
    print("session history: ", fetch_chat_history_for_each_session(session_id,db))
    return fetch_chat_history_for_each_session(session_id,db)

@router.delete("/delete-session/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    return delete_chat_history_by_session(session_id, db)
@router.delete("/delete-all")
def delete_all_sessions(db: Session = Depends(get_db)):
    return clear_all_chat_history(db)

# Dependency to get PostgresStore instance
def get_postgres_store(db: Session = Depends(get_db)) -> PostgresStore:
    return PostgresStore(db=db)
