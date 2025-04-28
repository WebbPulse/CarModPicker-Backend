from pydantic import BaseModel
from typing import Optional

# Schema for request body when creating/updating an item
class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None

# Schema for response body when reading an item
class ItemRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True # For Pydantic V2 compatibility with ORM models