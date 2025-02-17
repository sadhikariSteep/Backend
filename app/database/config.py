# app/database.py
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Load enviroment variable like database from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
# print(DATABASE_URL)

# The engine is the starting point for any SQLAlchemy database operations, and it manages the connection to the database.
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=5)

# This line creates a new Session factory configured with:
#       Changes to the database will not be automatically committed 
#       disables automatic flushing of pending changes to the database before a query is executed.
#       This binds the session to the previously created engine, which means all operations performed 
#                   through this session will interact with the specified database.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# This creates a declarative base class, which is the foundation for 
#       defining ORM models (Python classes that represent database tables). 
#       Each model will inherit from this base class.

Base = declarative_base()


def get_db():
    """
    This function is a dependency that returns a database session.
    """
    db = SessionLocal() # new session  is created.
    try:
        yield db # yield is used to create a generator function
        
    # After the caller is done using the session, this block 
    # ensures that the session is properly closed, releasing any resources associated with it. This is crucial for avoiding database connection leaks.
    finally:
        db.close()