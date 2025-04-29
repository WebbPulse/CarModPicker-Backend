from pydantic import BaseModel
from typing import Optional

# Schema for request body when creating/updating a car
class CarCreate(BaseModel):
    make: str
    model: str
    year: int

# Schema for request body when updating a car (all fields optional)
class CarUpdate(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None

# Schema for response body when reading a car
class CarRead(BaseModel):
    id: int
    make: str
    model: str
    year: int

    class Config:
        from_attributes = True # For Pydantic V2 compatibility with ORM models