# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime

# class UserCreate(BaseModel):
#     name: str
#     email: EmailStr
#     password: str

#     class Config:
#         from_attributes=True

# Define the request schema
class UserCreate(BaseModel):
    id: int
    email: EmailStr
    name: str
    steep_id: int

    class Config:    
        from_attributes=True

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes=True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    class Config:
        from_attributes=True

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True