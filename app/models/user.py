from sqlalchemy import Column, Integer, String, DateTime, Enum
from datetime import datetime
from sqlalchemy.orm import relationship
import enum

from app.database.database import Base


class RoleEnum(str, enum.Enum):
    USER = "user"

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.USER)

    wishlists = relationship("Wishlist", back_populates="owner", cascade="all, delete-orphan")
