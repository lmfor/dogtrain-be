from sqlalchemy import Column, Integer, String
from database import Base

class TestClass(Base):
    __tablename__ = "test"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    tag = Column(String, nullable=False)