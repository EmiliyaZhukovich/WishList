from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from fastapi import HTTPException, status

from app.repositories.wishlist_repo import WishlistRepository
from app.schemas.present import PresentResponse, PresentCreate, PresentUpdate
from app.repositories.present_repo import PresentRepository
from app.repositories.user_repo import UserRepository

class PresentService:
    def __init__(self, session: AsyncSession):
        self.present_repo = PresentRepository(session)
        self.user_repo = UserRepository(session)
        self.wishlist_repo = WishlistRepository(session)

    async def get_presents(self) -> List[PresentResponse]:
        presents = await self.present_repo.get_all_presents()
        return [PresentResponse.model_validate(present) for present in presents]

    async def get_present_by_id(self, present_id: int) -> PresentResponse:
        present = await self.present_repo.get_present_by_id(present_id)
        if not present:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Present not found")
        return PresentResponse.model_validate(present)

    async def create_present(self, data: PresentCreate) -> PresentResponse:
        wishlist = await self.wishlist_repo.get_wishlist_by_id(data.wishlist_id)
        if not wishlist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")
        present = await self.present_repo.create_present(data.dict())
        return PresentResponse.model_validate(present)

    async def update_present(self, present_id: int, data: PresentUpdate) -> PresentResponse:
        if data.wishlist_id is not None:
            wishlist = await self.wishlist_repo.get_wishlist_by_id(data.wishlist_id)
            if not wishlist:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")
        present = await self.present_repo.get_present_by_id(present_id)
        if not present:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Present not found")
        for key, value in data.dict(exclude_unset=True).items():
            setattr(present, key, value)
        await self.present_repo.session.commit()
        await self.present_repo.session.refresh(present)
        return PresentResponse.model_validate(present)

    async def delete_present(self, present_id: int) -> None:
        success = await self.present_repo.delete_present(present_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Present not found")
