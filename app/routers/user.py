from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.services.user import UserService
from app.schemas.user import UserResponse, UserCreate
from app.core.limit import limiter

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/login")
@limiter.limit("2/minute")
async def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
):
    token = await UserService(session).authenticate(
        form.username,
        form.password
    )
    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("2/minute")
async def register_user(
    request: Request,
    user_data: UserCreate,
    session: AsyncSession = Depends(get_db),
):
    user = await UserService(session).create_user(user_data)
    return user
