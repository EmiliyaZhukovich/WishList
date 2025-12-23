from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from datetime import datetime
from sqlalchemy.orm import relationship

from app.database.database import Base

class Wishlist(Base):
    __tablename__ = 'wishlists'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable = False)
    description = Column(String, nullable = True)
    event_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    presents = relationship("Present", back_populates="wishlist", cascade="all, delete-orphan")
    owner = relationship("User", back_populates="wishlists")
