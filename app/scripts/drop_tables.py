from Backend.app.database.config import engine, Base
from sqlalchemy import Table, MetaData

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
    chat_table = Table('chats', metadata, autoload_with=engine)

    # Drop the tables
    user_table.drop(bind=engine)
    chat_table.drop(bind=engine)

    print("Specific tables dropped successfully.")
if __name__ == "__main__":
    #drop_specific_tables()
    drop_tables()
