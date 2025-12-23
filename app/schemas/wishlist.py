from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class WishlistBase(BaseModel):
    name:str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    event_date: Optional[date] = None

class WishlistCreate(WishlistBase):
    user_id: Optional[int] = None

class WishlistUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    event_date: Optional[str] = None

class WishlistResponse(WishlistBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
