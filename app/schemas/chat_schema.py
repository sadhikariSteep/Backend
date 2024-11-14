# app/schemas/chat.py
from pydantic import BaseModel
from datetime import datetime

class ChatCreate(BaseModel):
    user_id: int
    session_id: str
    question: str
    response: str

    class Config:
        from_attributes=True

class ChatResponse(BaseModel):
    id: int
    user_id: int
    session_id: str
    question: str
    response: str
    timestamp: datetime

    class Config:
        from_attributes=True

        
class ChatRequest(BaseModel):
    question: str
    
    class Config:
        from_attributes=True