from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.schemas.user import UserResponse, UserCreate
from app.repositories.user_repo import UserRepository
from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token

class UserService:
    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)

    async def get_users(self) -> List[UserResponse]:
        users = await self.user_repo.get_all_users()
        return [UserResponse.model_validate(user) for user in users]

    async def get_user_by_id(self, user_id: int) -> UserResponse:
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserResponse.model_validate(user)

    async def create_user(self, data: UserCreate) -> UserResponse:
        existing_email = await self.user_repo.get_user_by_email(data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        user_data = data.model_dump(exclude={"password"})
        user_data["hashed_password"] = hash_password(data.password)

        try:
            user = await self.user_repo.create_user(user_data)
            return UserResponse.model_validate(user)
        except IntegrityError as e:
            if "email" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists"
                )
            elif "username" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this username already exists"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Database integrity error"
                )

    async def authenticate(self, username: str, password: str) -> str:
        user = await self.user_repo.get_user_by_email(username)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = await create_access_token({"sub": str(user.id)})
        return token
