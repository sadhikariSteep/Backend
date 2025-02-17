
import sys
import os

# Get the path to the backend directory
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))

# Add the backend directory to the Python path
sys.path.append(backend_dir)

from app.database.config import engine, Base
from sqlalchemy import Table, MetaData
from app.models.models import User, ChatHistory  # Import your models here

metadata = MetaData()

# Reflect the existing tables
metadata.reflect(bind=engine)

def drop_tables():
    # Drop all tables in the database
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped successfully.")

def drop_specific_tables():
    # Specify the tables you want to drop
    user_table = Table('users', metadata, autoload_with=engine)
    chat_table = Table('chat_history', metadata, autoload_with=engine)

    # Drop the tables
    user_table.drop(bind=engine)
    chat_table.drop(bind=engine)

    print("Specific tables dropped successfully.")
if __name__ == "__main__":
    #drop_specific_tables()
    drop_tables()
