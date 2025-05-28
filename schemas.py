from pydantic import BaseModel, Field
from typing import List
from uuid import UUID


# Response/Return models
class UserIn(BaseModel):
    username : str = Field(..., description="Desired Username")

class UserCreate(BaseModel):
    id: int = Field(...)
    username: str = Field(...)
    token: UUID

    class Config:
        orm_mode = True

class UserOut(BaseModel):
    id: int
    username: str
    token: UUID

    class Config: # JSON. which means we will return UserOUT
        orm_mode = True