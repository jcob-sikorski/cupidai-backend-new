from typing import Annotated, Optional

from fastapi import Depends, APIRouter, Path, HTTPException, Form
from fastapi.security import OAuth2PasswordRequestForm

from model.account import Account, Token

from service import account as service

router = APIRouter(prefix="/account")

@router.post("/update-session")
async def update_session(user: Annotated[Account, Depends(service.get_current_active_user)]) -> Token:
    return await service.update_session(user)

@router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    return await service.login(form_data)


@router.post("/signup")
async def signup(email: str,
                 form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    return await service.signup(email, 
                                form_data)


@router.post("/signup-ref")
async def signup_ref(email: str,
                     referral_id: str,
                     form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    return await service.signup_ref(email, 
                                    referral_id, 
                                    form_data)

@router.post("/change-password", status_code=200)
async def change_password(password_reset_id: str, 
                          password: str) -> None:
    return service.change_password(password_reset_id, password)


@router.post("/request-one-time-link", status_code=200)
async def request_one_time_link(email: dict) -> None:
    email = email.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email field is required")
    
    return service.request_one_time_link(email)

# TODO: we should do authentication of new email

@router.patch("/email", status_code=200)  # Changes the account's email
async def change_email(email: dict,
                       user: Annotated[Account, Depends(service.get_current_active_user)]) -> None:
    email = email.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email field is required")
    return service.change_email(email, user)


@router.get("/", response_model=Account)
async def get(user: Annotated[Account, Depends(service.get_current_active_user)]) -> Optional[Account]:
    user_without_password = Account(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            profile_uri=user.profile_uri,
            disabled=user.disabled
        )
    
    return user_without_password


@router.patch("/profile-picture", status_code=200)  # Changes the profile picture
async def change_profile_picture(profile_uri: dict, 
                                 user: Annotated[Account, Depends(service.get_current_active_user)]) -> None:
    
    profile_uri = profile_uri.get("profile_uri")
    if not profile_uri:
        raise HTTPException(status_code=400, detail="Profile URI is required")
    
    return service.change_profile_picture(profile_uri, user)


@router.delete("/", status_code=204)  # Deletes the account, status 204 for No Content
async def delete(user: Annotated[Account, Depends(service.get_current_active_user)]) -> None:
    return service.delete(user)
