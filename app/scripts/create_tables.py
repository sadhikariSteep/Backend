import sys
import os

# Get the path to the backend directory
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))

# Add the backend directory to the Python path
sys.path.append(backend_dir)

from app.database.config import engine, Base
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from app.models.models import User, ChatHistory, pgDocument  # should always be imported if u want to create tables

# Test if we can connect to the database
try:
    # Test if the connection to the engine works
    with engine.connect() as connection:
        print("Successfully connected to the database.")
except SQLAlchemyError as e:
    print(f"Error connecting to the database: {e}")

# Create the tables
def create_tables():
    try:
        Base.metadata.create_all(bind=engine)  # Create tables based on the models
        print("Tables created successfully.")
    except SQLAlchemyError as e:
        print(f"Error creating tables: {e}")

# Check the existing tables
def check_existing_tables():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Existing tables in the database: {tables}")
    return tables

if __name__ == "__main__":
    create_tables()
    tables = check_existing_tables()
    print(f"Tables in the database after creation: {tables}")