from pydantic import BaseModel, Field
from enum import Enum

class RoleEnum(str, Enum):
    USER = "user"

class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    email: str = Field(..., max_length=100)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=72)
    role: RoleEnum = RoleEnum.USER


class UserResponse(UserBase):
    id: int
    role: RoleEnum

    class Config:
        from_attributes = True

