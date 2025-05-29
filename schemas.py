from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


# Response/Return models for USERS
class UserBase(BaseModel):
    username : str

class UserCreate(UserBase):
    password: str = Field(...,min_length=6)

class UserOut(UserBase):
    id: UUID
    token: UUID

    class Config: # JSON. which means we will return UserOUT
        orm_mode = True

    # ==== DOG SCHEMAS ====

class DogBase(BaseModel):
    name: str
    breed: str
    age: Optional[str] = None

class DogCreate(DogBase):
    owner_id: UUID

class DogUpdate(BaseModel):
    name: Optional[str]
    breed: Optional[str]
    age: Optional[str]

class DogOut(DogBase):
    id: UUID
    owner_id: UUID

    class Config:
        orm_mode = True