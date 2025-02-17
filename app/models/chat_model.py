from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from sqlalchemy.orm import relationship
from app.database import Base

# class ChatHistory(Base):
#     __tablename__ = "chat_history"
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     session_id = Column(String, nullable=False)
#     question = Column(String, nullable=False)
#     response = Column(String, nullable=False)
#     timestamp = Column(DateTime, default=datetime.now())
#     timestamp_response = Column(DateTime, default=datetime.now())

#     user = relationship("User", back_populates="chat_history")