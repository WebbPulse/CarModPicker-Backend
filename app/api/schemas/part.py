from pydantic import BaseModel, ConfigDict
from typing import Optional


# Schema for request body when creating/updating a part
class PartCreate(BaseModel):
    name: str
    part_type: Optional[str] = None
    part_number: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    image_url: Optional[str] = None
    build_list_id: int


# Schema for request body when updating a part (all fields optional)
class PartUpdate(BaseModel):
    name: Optional[str] = None
    part_type: Optional[str] = None
    part_number: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    image_url: Optional[str] = None
    build_list_id: Optional[int] = None


# Schema for response body when reading a part
class PartRead(BaseModel):
    id: int
    name: str
    part_type: Optional[str] = None
    part_number: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    image_url: Optional[str] = None
    build_list_id: int

    model_config = ConfigDict(from_attributes=True)
