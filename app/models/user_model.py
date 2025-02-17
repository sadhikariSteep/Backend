from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from sqlalchemy.orm import relationship
from app.database import Base
import enum

# class UserRole(str, enum.Enum):
#     admin = "admin"
#     user = "user"

# class User(Base):
#     __tablename__ = 'users'
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, index=True)
#     hashed_password = Column(String, nullable=False)
#     email = Column(String, unique=True, index=True)
#     created_at = Column(DateTime, default=datetime.now)
#     #role = Column(enum.Enum(UserRole), default=UserRole.user)  # Default role is user

#     chats = relationship("chat_history",back_populates="user")
