from fastapi import APIRouter, Depends, BackgroundTasks

from pydantic import BaseModel

from typing import Annotated, List

from model.account import Account
from model.deepfake import Message

from service import account as account_service
from service import facefusion_deepfake as service

router = APIRouter(prefix="/facefusion-deepfake")

@router.post("/webhook", status_code=200)
async def webhook(message: Message) -> None:
    print("FACEFUSION WEBHOOK ACTIVATED")
    print(message)
    service.webhook(message)


class FacefusionGenerateRequest(BaseModel):
    source_uris: str
    target_uri: str
  

# TODO: accept array of target uris and return an array of job_ids?? how would this work?
@router.post("/generate", status_code=201)
async def generate(req: FacefusionGenerateRequest,
                   user: Annotated[Account, Depends(account_service.get_current_active_user)],
                   background_tasks: BackgroundTasks) -> str:
    return service.run_video_faceswap(req.source_uris, 
                                      req.target_uri,
                                      user,
                                      background_tasks)