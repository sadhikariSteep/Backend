from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, BigInteger, JSON
from sqlalchemy.orm import relationship
from app.database.config import Base  # Import Base from the correct module
from sqlalchemy.dialects.postgresql import JSONB

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    steep_id = Column(BigInteger, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    
    # Define relationship to ChatHistory model
    chat_history = relationship("ChatHistory", back_populates="user")

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    session_id = Column(String, nullable=False)
    question = Column(String, nullable=False)
    response = Column(JSON, nullable=True)
    timestamp_query = Column(DateTime, default=datetime.now())
    timestamp_response = Column(DateTime, default=datetime.now())


    # Define relationship to User model
    user = relationship("User", back_populates="chat_history")

class pgDocument(Base):
    __tablename__ = "docstore"
    key = Column(String, primary_key=True)
    value = Column(JSONB)
    
    def __repr__(self):
        return f"<SQLDocument key='{self.key}', value='{self.value}')"
