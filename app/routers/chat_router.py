# app/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.chat_schema import ChatCreate, ChatResponse, ChatRequest
from app.crud.chat_crud import create_chat, get_chats_by_user
from app.crud.user_crud import get_user_by_email  # To verify user existence
from app.crud import chat_crud as crud_chat
from app.crud import user_crud as crud_user
from app.database.config import get_db
from langchain_ollama import OllamaLLM
from app.utils.chain_manager import *
from app.utils.docu_manager import *
from app.utils.embed_manager import *
from app.utils.dependencies import *

document_manager = DocumentManager(directory_path="app/Data")
embedding_manager = None
conversation_chain_manager = None


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)
llama = OllamaLLM(model="llama3.1:8b", base_url='http://ollama-container:11434')



import requests
from fastapi import FastAPI, Response

@router.get("/request")#, response_model=ChatResponse)
async def chat(prompt: str):
    response = llama(prompt)
    #print("got the response from llam: " ,response)
    # Optionally save the message to the database
    #create_chat(request.message)
    #return ChatResponse(response=response.text)
    return response
    # res = requests.post('http://ollama:11434/api/generate', json={
    #     "prompt": prompt,
    #     "stream" : False,
    #     "model" : "llama3.1:8b"
    # })

    return Response(content=res.text, media_type="application/json")


@router.post("/", response_model=ChatResponse)
def create_chat(chat: ChatCreate, db: Session = Depends(get_db)):
    # Verify if the user exists
    user = crud_user.get_user_by_id(db=db, user_id=chat.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    return crud_chat.create_chat(db=db, chat=chat)

@router.get("/{user_id}", response_model=List[ChatResponse])
def read_chats(user_id: int, db: Session = Depends(get_db)):
    chats = get_chats_by_user(db, user_id=user_id)
    return chats


    
@router.post("/query")
async def chat_with_bot(request: ChatRequest, vectordb=Depends(get_vectordb), embedding_manager=Depends(get_embedding_manager)):
    conversational_manager = ConversationalChainManager(vectordb)
    chain = conversational_manager.build_conversation_chain()

    response = chain.invoke({"input":request.question},
                                                config={"configurable": {"session_id": "abc123"}}, 
                                                )
    print(response["answer"])
    return {"response": response["answer"]}

