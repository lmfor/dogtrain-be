from sqlalchemy import Column, Integer, String
from database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True,index=True)
    username = Column(String, unique=True,index=True,nullable=False)
    token = Column      (
        UUID(as_uuid=True),
        primary_key=False,
        default=uuid.uuid4,
        unique=True,
        index=True,
        nullable=False
    )
