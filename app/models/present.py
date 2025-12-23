from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.database import Base

class Present(Base):
    __tablename__ = 'presents'

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True, nullable = False)
    name = Column(String, index=True, nullable = False)
    price = Column(Numeric(10, 2), nullable = True)
    description = Column(String, nullable = True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    wishlist_id = Column(Integer, ForeignKey('wishlists.id'), nullable=False)


    wishlist = relationship("Wishlist", back_populates="presents")
