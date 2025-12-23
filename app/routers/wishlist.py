from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.services.wishlist import WishlistService
from app.schemas.wishlist import WishlistResponse, WishlistCreate, WishlistUpdate
from app.security.dependencies import get_current_user, require_user_role
from app.models.user import User
from app.core.limit import limiter


router = APIRouter(
    prefix="/api/wishlist",
    tags=["wishlist"]
)

@router.get("/", response_model=List[WishlistResponse], status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def get_wishlists(request: Request, db:Session = Depends(get_db), current_user=Depends(get_current_user), user: User = Depends(require_user_role)):
    wishlist_service = WishlistService(db)
    return await wishlist_service.get_wishlists()

@router.get("/{wishlist_id}", response_model=WishlistResponse, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def get_wishlist(request: Request,wishlist_id: int, db:Session = Depends(get_db), current_user=Depends(get_current_user), user: User = Depends(require_user_role)):
    wishlist_service = WishlistService(db)
    return await wishlist_service.get_wishlist_by_id(wishlist_id)

@router.post("/", response_model = WishlistResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_wishlist(request: Request,wishlist: WishlistCreate, db:Session = Depends(get_db), current_user=Depends(get_current_user), user: User = Depends(require_user_role)):
    wishlist_data = wishlist.model_dump()
    wishlist_data["user_id"] = current_user.id
    wishlist_service = WishlistService(db)
    return await wishlist_service.create_wishlist(wishlist_data)

@router.put("/{wishlist_id}", response_model=WishlistResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def update_wishlist(request: Request,wishlist_id: int, wishlist: WishlistUpdate, db:Session = Depends(get_db), current_user=Depends(get_current_user), user: User = Depends(require_user_role)):
    wishlist_data = wishlist.model_dump()
    wishlist_data["user_id"] = current_user.id
    wishlist_service = WishlistService(db)
    return await wishlist_service.update_wishlist(wishlist_id, wishlist_data)

@router.delete("/{wishlist_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_wishlist(request: Request,wishlist_id: int, db:Session = Depends(get_db), current_user=Depends(get_current_user), user: User = Depends(require_user_role)):
    wishlist_service = WishlistService(db)
    await wishlist_service.delete_wishlist(wishlist_id)
