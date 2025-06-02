from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional


# Schema for request body when creating a user
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


# Schema for request body when updating a user
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    disabled: Optional[bool] = None
    password: Optional[str] = None


# Schema for response body when reading a user (DO NOT include password)
class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    disabled: bool
    email_verified: bool

    model_config = ConfigDict(from_attributes=True)
