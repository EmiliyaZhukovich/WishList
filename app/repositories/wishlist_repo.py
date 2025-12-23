from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.wishlist import Wishlist

class WishlistRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_wishlist_by_id(self, wishlist_id: int) -> Optional[Wishlist]:
        result = await self.session.execute(
            select(Wishlist).where(Wishlist.id == wishlist_id)
        )
        return result.scalars().first()

    async def get_all_wishlists(self) -> List[Wishlist]:
        result = await self.session.execute(select(Wishlist))
        return result.scalars().all()

    async def create_wishlist(self, data: Dict[str, Any]) -> Wishlist:
        new_wishlist = Wishlist(**data)
        self.session.add(new_wishlist)
        await self.session.commit()
        await self.session.refresh(new_wishlist)
        return new_wishlist

    async def update_wishlist(self, wishlist_id: int, data: Dict[str, Any]) -> Optional[Wishlist]:
        wishlist = await self.get_wishlist_by_id(wishlist_id)
        if not wishlist:
            return None
        for key, value in data.items():
            setattr(wishlist, key, value)
        await self.session.commit()
        await self.session.refresh(wishlist)
        return wishlist

    async def delete_wishlist(self, wishlist_id: int) -> bool:
        wishlist = await self.get_wishlist_by_id(wishlist_id)
        if not wishlist:
            return False
        await self.session.delete(wishlist)
        await self.session.commit()
        return True
