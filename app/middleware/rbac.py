# app/middleware/rbac.py
from fastapi import HTTPException, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from app.crud.user_crud import get_user_by_email
from sqlalchemy.orm import Session
from app.database.config import get_db
from jose import JWTError, jwt
from dotenv import load_dotenv
import os
from dataclasses import dataclass
import bcrypt

#----------------------------------------------------#
#           no attribute '__about__                  #
#----------------------------------------------------#
@dataclass
class SolveBugBcryptWarning:
    __version__: str = getattr(bcrypt, "__version__")

setattr(bcrypt, "__about__", SolveBugBcryptWarning())

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Load enviroment variable like database from .env
load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # bcrypt argon2


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email:str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

        
    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    
    return pwd_context.verify(plain_password, hashed_password)


# async def admin_required(current_user: User = Depends(get_current_user)):
#     if current_user.role != UserRole.admin:
#         raise HTTPException(status_code=403, detail="Operation forbidden")
