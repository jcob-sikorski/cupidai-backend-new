from fastapi import APIRouter, Depends, HTTPException

from typing import Annotated

from model.account import Account

from service import account as account_service
from service import bug as service

router = APIRouter(prefix="/bug")



@router.post("/", status_code=201)  # Creates a bug report
async def create(description: dict, 
                 user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> None:
    description = description.get("description")
    if not description:
        raise HTTPException(status_code=400, detail="Description field is required")

    return service.create(description, user)
