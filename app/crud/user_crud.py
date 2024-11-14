# app/crud/user.py
from sqlalchemy.orm import Session
from app.models.user_model import User
from app.schemas.user_schema import UserCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_email(db: Session, email: str):
    """
    Retrieve a user from the database by their email address.
    """
    # print("our user:", email)
    # all_users = db.query(User).all()
    # email_adress = [user.email for user in all_users]
    # print("Now all db user:", email_adress)
    # filter_user = db.query(User).filter(User.email == email).first()
    # print("filter user:", f"user found: {filter_user.email}" if filter_user else f"no user found with email: {email}")

    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    """
    Retrieve a user from the database by their ID.
    """
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserCreate):
    """
    Create a new user in the database.
    """
    hashed_password = pwd_context.hash(user.password)
    db_user = User(name=user.name, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 10):
    """
    Retrieve a list of users from the database with pagination.
    """
    return db.query(User).offset(skip).limit(limit).all()
