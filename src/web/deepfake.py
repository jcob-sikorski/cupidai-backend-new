from fastapi import APIRouter, Depends

from typing import List, Optional, Annotated

from pydantic import BaseModel

from model.account import Account
from model.deepfake import Message

from service import account as account_service
from service import deepfake as service

router = APIRouter(prefix="/deepfake")


class GeneratePhotoRequest(BaseModel):
    source_uri: str
    target_uri: str


@router.post("/photo", status_code=201)
async def photo_faceswap(req: GeneratePhotoRequest,
                         user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[Message]:
    
    return service.photo_faceswap(req.source_uri, 
                                  req.target_uri,
                                  user)


class GenerateVideoRequest(BaseModel):
    source_uri: str
    target_uuid: str
    target_filename: str

@router.post("/video", status_code=201)
async def video_faceswap(req: GenerateVideoRequest,
                         user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[Message]:
    
    return service.video_faceswap(req.source_uri, 
                                  req.target_uuid,
                                  req.target_filename,
                                  user)

@router.get("/message", status_code=200)  # Retrieves history
async def get_message(job_id: str,
                      _: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[Message]:
    return service.get_message(job_id)


@router.get("/history", status_code=200)  # Retrieves history
async def get_history(user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[List[Message]]:
    return service.get_history(user)
