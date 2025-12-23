from pydantic import BaseModel, Field
from typing import Optional

class PresentBase(BaseModel):
    url: str = Field(..., max_length=255)
    name: str = Field(..., max_length=100)
    price: Optional[float] = None
    description: Optional[str] = Field(None, max_length=255)

class PresentCreate(PresentBase):
    wishlist_id: int

class PresentUpdate(BaseModel):
    url: Optional[str] = Field(None, max_length=255)
    name: Optional[str] = Field(None, max_length=100)
    price: Optional[float] = None
    description: Optional[str] = Field(None, max_length=255)
    wishlist_id: Optional[int] = None

class PresentResponse(PresentBase):
    id: int
    wishlist_id: int

    class Config:
        from_attributes = True
