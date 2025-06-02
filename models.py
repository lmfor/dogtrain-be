from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float
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
    role = Column(String, default="client")  # "client" or "trainer"
    
    # Trainer specific fields
    experience = Column(Integer, nullable=True)
    specialties = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)

    dogs = relationship("Dog", back_populates="owner")
    trainer_locations = relationship("TrainerLocation", back_populates="trainer")

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password) #type: ignore

    @classmethod
    def hash_password(cls, password: str) -> str:
        return pwd_context.hash(password)
    
    
class Dog(Base):
    __tablename__ = "dogs"

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


class TrainerLocation(Base):
    __tablename__ = "trainer_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String, nullable=True)
    
    trainer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    trainer = relationship("User", back_populates="trainer_locations")
