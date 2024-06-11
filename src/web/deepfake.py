from fastapi import APIRouter, Depends

from typing import List, Optional, Annotated

from model.account import Account
from model.deepfake import Message

from service import account as account_service
from service import deepfake as service

router = APIRouter(prefix="/deepfake")

@router.get("/message", status_code=200)  # Retrieves history
async def get_message(job_id: str,
                      _: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[Message]:
    return service.get_message(job_id)


@router.get("/history", status_code=200)  # Retrieves history
async def get_history(user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[List[Message]]:
    return service.get_history(user)
