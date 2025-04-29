from pydantic import BaseModel, EmailStr
from typing import Optional

# Schema for request body when creating a user
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    # password: str # Add password field if needed for creation

# Schema for request body when updating a user
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    disabled: Optional[bool] = None
    # password: Optional[str] = None # Add if password can be updated

# Schema for response body when reading a user
class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    disabled: bool # Represent disabled as boolean

    class Config:
        from_attributes = True # For Pydantic V2 compatibility with ORM models