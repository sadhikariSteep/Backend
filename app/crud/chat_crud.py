# app/crud/chat.py
from sqlalchemy.orm import Session
from app.models.chat_model import Chat
from app.schemas.chat_schema import ChatCreate

def create_chat(db: Session, chat: ChatCreate):
    db_chat = Chat(
        user_id=chat.user_id,
        session_id=chat.session_id,
        question=chat.question,
        response=chat.response
    )
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

def get_chats_by_user(db: Session, user_id: int):
    return db.query(Chat).filter(Chat.user_id == user_id).all()
