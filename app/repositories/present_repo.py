from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.present import Present

class PresentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_present_by_id(self, present_id: int) -> Optional[Present]:
        result = await self.session.execute(
            select(Present).where(Present.id == present_id)
        )
        return result.scalars().first()

    async def get_all_presents(self) -> List[Present]:
        result = await self.session.execute(select(Present))
        return result.scalars().all()

    async def create_present(self, data: Dict[str, Any]) -> Present:
        new_present = Present(**data)
        self.session.add(new_present)
        await self.session.commit()
        await self.session.refresh(new_present)
        return new_present

    async def update_present(self, present_id: int, data: Dict[str, Any]) -> Optional[Present]:
        present = await self.get_present_by_id(present_id)
        if not present:
            return None
        for key, value in data.items():
            setattr(present, key, value)
        await self.session.commit()
        await self.session.refresh(present)
        return present

    async def delete_present(self, present_id: int) -> bool:
        present = await self.get_present_by_id(present_id)
        if not present:
            return False
        await self.session.delete(present)
        await self.session.commit()
        return True
