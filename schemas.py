from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID


# Response/Return models for USERS
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: Optional[str] = "client"
    name: Optional[str] = None
    experience: Optional[int] = None
    specialties: Optional[str] = None
    phone: Optional[str] = None
    profile_picture: Optional[str] = None

class UserOut(UserBase):
    id: UUID
    token: UUID
    role: str
    experience: Optional[int] = None
    specialties: Optional[str] = None
    phone: Optional[str] = None
    profile_picture: Optional[str] = None

    class Config:
        from_attributes = True

# ==== TRAINER LOCATION SCHEMAS ====

class LocationBase(BaseModel):
    name: str
    latitude: float
    longitude: float
    address: Optional[str] = None

class LocationCreate(LocationBase):
    pass

class LocationUpdate(LocationBase):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None

class LocationOut(LocationBase):
    id: UUID
    trainer_id: UUID

    class Config:
        from_attributes = True

# ==== DOG SCHEMAS ====

class DogBase(BaseModel):
    name: str
    breed: str
    age: Optional[str] = None

class DogCreate(DogBase):
    owner_id: UUID

class DogUpdate(BaseModel):
    name: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[str] = None

class DogOut(DogBase):
    id: UUID
    owner_id: UUID

    class Config:
        from_attributes = True