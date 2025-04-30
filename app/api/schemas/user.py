from pydantic import BaseModel, EmailStr
from typing import Optional

# Schema for request body when creating a user
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

# Schema for request body when updating a user
class UserUpdate(BaseModel):
    id: int
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    disabled: Optional[bool] = None
    password: Optional[str] = None

# Schema for response body when reading a user (DO NOT include password)
class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    disabled: bool

    class Config:
        from_attributes = True