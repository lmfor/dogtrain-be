from pydantic import BaseModel, Field
from typing import List

# Response/Return models

class TestCreateIn(BaseModel): # input class
    description: str = Field(...)
    tag: str = Field(...)

class TestCreateOut(BaseModel): # output class
    id: int = Field(...)
    description: str = Field(...)
    tag: str = Field(...)

    class Config: # lets pydantic know that this model is compatible with ORM models --> JSON
        orm_mode = True

class TestReadOut(BaseModel): # output class for reading
    id: int
    description: str
    tag: str

    class Config:
        orm_mode = True