from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.security.jwt import decode_access_token
from app.repositories.user_repo import UserRepository
from app.security.oauth2 import oauth2_scheme
from app.models.user import User, RoleEnum

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
):
    payload = await decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = int(payload["sub"])
    user = await UserRepository(session).get_user_by_id(user_id)

    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user

async def require_user_role(
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [RoleEnum.USER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user
