from fastapi import APIRouter, Depends, BackgroundTasks

from typing import Annotated, Dict, Optional

from model.account import Account
from model.image_generation import Settings, Message

from service import account as account_service
import service.image_generation as service

router = APIRouter(prefix="/image-generation")


@router.post("/webhook", status_code=200)
async def webhook(message: Message) -> None:
    print("COMFYUI WEBHOOK ACTIVATED")
    return service.webhook(message)


@router.post("/generate", status_code=201)
async def generate(settings: Settings,
                   user: Annotated[Account, Depends(account_service.get_current_active_user)], 
                   background_tasks: BackgroundTasks) -> None:
    
    print("SETTINGS PASSED FROM FRONTEND", settings)

    return await service.generate(settings, 
                                  user, 
                                  background_tasks)


@router.get("/recent-batch", status_code=200)  # Retrieves most recent batch
async def get_batch(user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[Message]:
    return service.get_batch(user)