from sqlalchemy import Column, Integer, LargeBinary, JSON, Table
from app.database import Base

class FaissIndexTable(Base):
    __tablename__ = 'faiss_index'

    id = Column(Integer, primary_key=True, index=True)
    index_data = Column(LargeBinary, nullable=False)
    metadata = Column(JSON, nullable=True)