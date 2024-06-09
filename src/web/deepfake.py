from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel

from typing import List, Optional, Annotated

from model.account import Account
from model.deepfake import Message

from service import account as account_service
from service import deepfake as service

router = APIRouter(prefix="/deepfake")

@router.post("/webhook", status_code=200)
async def webhook(response: dict) -> None:
    print("AKOOL WEBHOOK ACTIVATED")
    print(response)
    try:
        service.webhook(response)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid signature.")


class AkoolGeneratePhotoRequest(BaseModel):
    source_uri: str
    target_uri: str

@router.post("/photo", status_code=201)
async def generate_photo(req: AkoolGeneratePhotoRequest,
                         user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[Message]:
    return service.initiate_photo_faceswap(req.source_uri, 
                                           req.target_uri,
                                           user)


class AkoolGenerateVideoRequest(BaseModel):
    source_uri: str
    target_uri: str
    video_uri: str

@router.post("/video", status_code=201)
async def generate_video(req: AkoolGenerateVideoRequest,
                         user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[Message]:
    print("GOT THE REQUEST")
    return service.initiate_video_faceswap(req.source_uri, 
                                           req.target_uri,
                                           req.video_uri,
                                           user)


@router.get("/message", status_code=200)  # Retrieves history
async def get_message(job_id: str,
                      _: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[Message]:
    return service.get_message(job_id)


@router.get("/history", status_code=200)  # Retrieves history
async def get_history(user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[List[Message]]:
    return service.get_history(user)
