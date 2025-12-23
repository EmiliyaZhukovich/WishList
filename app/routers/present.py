from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.services.present import PresentService
from app.schemas.present import PresentResponse, PresentCreate, PresentUpdate
from app.security.dependencies import get_current_user, require_user_role
from app.models.user import User
from app.core.limit import limiter

router = APIRouter(
    prefix="/api/present",
    tags=["present"]
)

@router.get("/", response_model=List[PresentResponse], status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def get_presents(request: Request,db:Session = Depends(get_db), current_user=Depends(get_current_user), user: User = Depends(require_user_role)):
    present_service = PresentService(db)
    return await present_service.get_presents()

@router.get("/{present_id}", response_model=PresentResponse, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def get_present(request: Request,present_id: int, db:Session = Depends(get_db), current_user=Depends(get_current_user), user: User = Depends(require_user_role)):
    present_service = PresentService(db)
    return await present_service.get_present_by_id(present_id)

@router.post("/", response_model = PresentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_present(request: Request,present: PresentCreate, db:Session = Depends(get_db), current_user=Depends(get_current_user), user: User = Depends(require_user_role)):
    present_service = PresentService(db)
    return await present_service.create_present(present)

@router.put("/{present_id}", response_model=PresentResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def update_present(request: Request,present_id: int, present: PresentUpdate, db:Session = Depends(get_db), current_user=Depends(get_current_user), user: User = Depends(require_user_role)):
    present_service = PresentService(db)
    return await present_service.update_present(present_id, present)

@router.delete("/{present_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_present(request: Request,present_id: int, db:Session = Depends(get_db), current_user=Depends(get_current_user), user: User = Depends(require_user_role)):
    present_service = PresentService(db)
    await present_service.delete_present(present_id)
