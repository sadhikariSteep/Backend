# app/routers/user.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.schemas.user_schema import UserCreate, UserResponse, LoginRequest, LoginResponse
from app.crud.user_crud import get_user_by_email, create_user, get_users
from app.middleware.rbac import get_current_user, create_access_token, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES
from app.database.config import get_db
from datetime import datetime, timedelta
from fastapi.encoders import jsonable_encoder



router = APIRouter(
    prefix="/auth",
    tags=["/auth"],
)

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    print("Received user data:", user)  # Log incoming data for debugging
    existing_user = get_user_by_email(db, email=user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_user(db=db, user=user)

@router.get("users/me", response_model=UserResponse)
def read_current_user(current_user: UserResponse=Depends(get_current_user)):
    return current_user




@router.post("/login", response_model=LoginResponse)
async def verifyLogin(user: LoginRequest, db: Session= Depends(get_db)):

    try:
        # retrive user by email
        db_user = get_user_by_email(db, email=user.email)
        print("filter user:", f"user found: {db_user.email}" if db_user else f"no user found with email: {user.email}")

        # Check if user exists
        if db_user is None:
            raise HTTPException(status_code=400, detail="Invalid email ..or password")

        # Verify the password
        # if not verify_password(user.password, db_user.hashed_password):  # Assuming db_user.hashed_password stores the hashed password
        #     print("Password is incorrect.")
        #     raise HTTPException(status_code=400, detail="Invalid email or password")
        if verify_password(user.password, db_user.hashed_password):
            print("Password is correct!")

        else:
            print("Password is incorrect.")  
            raise HTTPException(status_code=400, detail="Invalid email or password")
        # Create and return access token
        # access_token_expires = timedelta(minutes=30)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": db_user.email}, expires_delta=access_token_expires)
    
        #return {"access_token": access_token, "token_type": "bearer"}
        # Construct the response including all required fields
        response_data = LoginResponse(
            access_token=access_token,
            token_type="bearer",
            id=db_user.id,
            name=db_user.name,
            email=db_user.email,
            created_at=db_user.created_at
        )
        response = (response_data)
        print("Response data:: ", response)
        return response
    except Exception as e:
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal ddServer Error")


    
@router.get("/users/")
def read_users(db: Session = Depends(get_db)):
    users = get_users(db)
    print("users: ", users)
    return users
