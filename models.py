from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from database import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from passlib.context import CryptContext
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    token = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, index=True)
    #test_column = Column(String, nullable=True)

    dogs = relationship("Dog", back_populates="owner")

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password) #type: ignore

    @classmethod
    def hash_password(cls, password: str) -> str:
        return pwd_context.hash(password)
    
    
class Dog(Base):
    __tablename__ = "dogs"

    # ← Make sure this is here (and imported)
    id = Column(UUID(as_uuid=True),
                primary_key=True,
                default=uuid.uuid4,
                unique=True,
                index=True)

    name     = Column(String, nullable=False)
    breed    = Column(String, nullable=False)
    age      = Column(String, nullable=True)

    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    owner    = relationship("User", back_populates="dogs")
