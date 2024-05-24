from fastapi import APIRouter, Depends, Request

from pydantic import BaseModel

from typing import Annotated, Optional, Dict, Any

from fastapi import HTTPException

import os

from model.account import Account
from model.billing import Plan, CheckoutSessionRequest

from service import account as account_service
import service.billing as service

router = APIRouter(prefix="/billing")


class FeatureRequest(BaseModel):
    feature: str

@router.post("/has-permissions", status_code=200)  # Retrieves the check of access tothe feature
async def has_permissions(req: FeatureRequest,
                          user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> bool:
    return service.has_permissions(req.feature,
                                   user)


@router.post('/create-radom-checkout-session', status_code=200)
async def create_radom_checkout_session(req: CheckoutSessionRequest,
                                        user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> None:
    return service.create_radom_checkout_session(req,
                                                 user)


@router.post('/webhook')
async def webhook(request: Request) -> None:
    radom_verification_key = request.headers.get("radom-verification-key")
    
    if ((os.getenv("MODE") == 'production' and radom_verification_key != os.getenv("RADOM_WEBHOOK_SECRET")) or
        (os.getenv("MODE") == 'staging' and radom_verification_key != os.getenv("RADOM_WEBHOOK_SECRET")) or
        (os.getenv("MODE") == 'development' and radom_verification_key != os.getenv("RADOM_WEBHOOK_SECRET"))):
        raise HTTPException(
            status_code=401,
            detail="Invalid verification key"
        )


    return await service.radom_webhook(request)

@router.post('/paypal-webhook')
async def paypal_webhook(request: Request) -> None:
    return await service.paypal_webhook(request)


@router.get("/paypal/obtain-uuid", status_code=200)  # Links user id with generated uuid which then is passed as custom_id in paypal button
async def paypal_obtain_uuid(user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[str]:
    return service.paypal_obtain_uuid(user)


@router.post("/cancel-plan", status_code=201)  # Attempts to cancel current plan of the user
async def cancel_plan(user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> bool:
    return service.cancel_plan(user)


@router.get("/available-plans", status_code=200)  # Retrieves all available plans
async def get_available_plans(user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[Dict[str, Any]]:
    plans = service.get_available_plans(user)

    print(plans)

    return plans


@router.get("/product", status_code=200)  # Retrieves the specific product
async def get_product(plan_id: str,
                      _: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[Plan]:
    product = service.get_product(plan_id=plan_id)

    print(product)

    return product