from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from fastapi import HTTPException, status
from datetime import date
import logging

from app.repositories.wishlist_repo import WishlistRepository
from app.schemas.wishlist import WishlistResponse, WishlistCreate, WishlistUpdate
from app.repositories.user_repo import UserRepository
from app.tasks.tasks import enqueue_welcome_email

logger = logging.getLogger(__name__)

class WishlistService:
    def __init__(self, session: AsyncSession):
        self.wishlist_repo = WishlistRepository(session)
        self.user_repo = UserRepository(session)

    async def get_wishlists(self) -> List[WishlistResponse]:
        wishlists = await self.wishlist_repo.get_all_wishlists()
        return [WishlistResponse.model_validate(wishlist) for wishlist in wishlists]

    async def get_wishlist_by_id(self, wishlist_id: int) -> WishlistResponse:
        wishlist = await self.wishlist_repo.get_wishlist_by_id(wishlist_id)
        if not wishlist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")
        return WishlistResponse.model_validate(wishlist)

    @staticmethod
    def parse_event_date(event_date_str):
        try:
            return date.fromisoformat(event_date_str)
        except Exception:
            return None

    async def create_wishlist(self, data: WishlistCreate) -> WishlistResponse:
        user = await self.user_repo.get_user_by_id(data["user_id"])
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if "event_date" in data and isinstance(data["event_date"], str):
            data["event_date"] = self.parse_event_date(data["event_date"])
        wishlist = await self.wishlist_repo.create_wishlist(data)

        try:
            job_id = enqueue_welcome_email(user.email, wishlist.name)
            if job_id:
                logger.info("Поставлена задача отправки приветственного письма, job_id=%s", job_id)
        except Exception as e:
            logger.error(f"Failed to enqueue email task: {str(e)}")
        return WishlistResponse.model_validate(wishlist)

    async def update_wishlist(self, wishlist_id: int, data: WishlistUpdate) -> WishlistResponse:
        user = await self.user_repo.get_user_by_id(data["user_id"])
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        wishlist = await self.wishlist_repo.get_wishlist_by_id(wishlist_id)
        if not wishlist:
            raise HTTPException(tatus_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")

        for key, value in data.items():
            if value is not None:
                setattr(wishlist, key, value)
        await self.wishlist_repo.session.commit()
        await self.wishlist_repo.session.refresh(wishlist)
        return WishlistResponse.model_validate(wishlist)

    async def delete_wishlist(self, wishlist_id: int) -> None:
        success = await self.wishlist_repo.delete_wishlist(wishlist_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")
