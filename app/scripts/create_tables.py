import sys
import os

# Get the path to the backend directory
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))

# Add the backend directory to the Python path
sys.path.append(backend_dir)

from app.database.config import engine, Base
from app.models.models import User, Chat


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    create_tables()