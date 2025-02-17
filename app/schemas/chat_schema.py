# app/schemas/chat.py
from pydantic import BaseModel
from datetime import datetime
from typing import List, Literal

class ChatCreate(BaseModel):
    user_id: int
    session_id: str
    question: str
    response: str

    class Config:
        from_attributes=True

        
class ChatRequest(BaseModel):
    question: str
    selectedModel: str
    
    class Config:
        from_attributes=True


class ContentBlock(BaseModel):
    type: Literal["text", "think", "botStatusMsg"]
    content: str

class ChatResponse(BaseModel):
    response: List[ContentBlock]
    # duration: float