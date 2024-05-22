from fastapi import APIRouter, Depends, HTTPException

from typing import Annotated, Optional, List, Tuple

from pydantic import BaseModel

from model.account import Account
from model.ai_verification import Prompt, SocialAccount
from model.midjourney import Message

from service import account as account_service
from service import ai_verification as service

router = APIRouter(prefix="/ai-verification")

# class FaceswapRequest(BaseModel):
#     source_uri: str
#     target_uri: str

# @router.post("/faceswap", status_code=201)  # Initiates a face swap
# async def faceswap(req: FaceswapRequest, 
#                    user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> None:
#     return await service.faceswap(req.source_uri,
#                                   req.target_uri,
#                                   user)

@router.post("/imagine", status_code=201)  # Initiates an imagination process
async def imagine(prompt: Prompt, 
                  user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> None:
    return await service.imagine(prompt, user)


class ActionRequest(BaseModel):
    messageId: str
    button: str

@router.post("/action", status_code=201)  # Initiates a specific action
async def action(req: ActionRequest, 
                 user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> None:
    return await service.action(req.messageId, 
                                req.button, 
                                user)

class AddAccountRequest(BaseModel):
      profile_uri: str
      name: str
      platform: str
      note: str
      prompt: str
      version: str
      style: str
      width: str
      height: str
      stop: str
      stylize: str
      seed: str

@router.post("/add-account", status_code=201)  # Adds new account with a prompt
async def add_account(req: AddAccountRequest,
                      user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[Tuple[SocialAccount, Prompt]]:
    
    social_account = SocialAccount(
        profile_uri=req.profile_uri,
        name=req.name,
        platform=req.platform,
        note=req.note
    )

    prompt = Prompt(
        prompt=req.prompt,
        version=req.version,
        style=req.style,
        width=req.width,
        height=req.height,
        stop=req.stop,
        stylize=req.stylize,
        seed=req.seed
    )

    return service.add_account(social_account,
                               prompt,
                               user)


@router.patch("/social-account", status_code=200)  # Updates social account information
async def update(social_account: SocialAccount,
                 _: Annotated[Account, Depends(account_service.get_current_active_user)]) -> None:
    return service.update_account(social_account)


@router.get("/social-accounts", status_code=200)  # Retrieves all social accounts
async def get(user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[List[SocialAccount]]:
    return service.get_accounts(user)


@router.patch("/prompt", status_code=200)  # Updates prompt information
async def update_prompt(prompt: Prompt,
                        _: Annotated[Account, Depends(account_service.get_current_active_user)]) -> None:
    # print("UPDATING PROMPT")
    return service.update_prompt(prompt)


@router.get("/prompts", status_code=200)  # Retrieves all prompts
async def get_prompts(user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[List[Prompt]]:
    return service.get_prompts(user)


@router.get("/message", status_code=200)  # Retrieves specific message
async def get_message(messageId: str,
                      _: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[Message]:
    return service.get_message(messageId)


@router.get("/history", status_code=200)  # Retrieves history
async def get_history(user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> List[Message]:
    return service.get_history(user)


# @router.delete("/message/{messageId}", status_code=204)  # Cancels a specific job, status 204 for No Content
# async def cancel_job(messageId: str, 
#                      user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> None:
#     return await service.cancel_job(messageId, user)
