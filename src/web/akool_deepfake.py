from fastapi import APIRouter, Depends, HTTPException

from pydantic import BaseModel

from typing import Optional, Annotated

from model.account import Account
from model.deepfake import Message

from service import account as account_service
from service import akool_deepfake as service

router = APIRouter(prefix="/akool-deepfake")

@router.post("/webhook", status_code=200)
async def webhook(response: dict) -> None:
    print("AKOOL WEBHOOK ACTIVATED")
    print(response)
    try:
        service.webhook(response)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid signature.")


class AkoolGenerateRequest(BaseModel):
    source_uri: str
    target_uri: str

# TODO:~accept array of target uris and return an array of job_ids?? how would this work?
@router.post("/generate", status_code=201)
async def generate(req: AkoolGenerateRequest,
                   user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[Message]:
    return service.generate(req.source_uri, 
                            req.target_uri,
                            user)