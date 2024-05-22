from fastapi import APIRouter, Depends

from pydantic import BaseModel

from typing import Annotated, Optional

from model.account import Account
from model.referral import PayoutSubmission

from service import account as account_service
from service import referral as service

router = APIRouter(prefix = "/referral")


@router.post("/generate-link", status_code=201)  # Generates a new link
async def generate_link(user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> str:
    return service.generate_link(user)


@router.post("/link-clicked", status_code=201)
async def link_clicked(referral_id: str) -> None:
    service.link_clicked(referral_id)

# TODO: we need to implement endpoint for substraction of earnings 
#       in the earning_col by the specifed amount

class PayoutRequest(BaseModel):
    paypal_email: str | None = None
    amount: float | None = None
    scheduled_time: str | None = None

@router.post("/request-payout", status_code=201)  # Requests a payout
async def request_payout(req: PayoutRequest, 
                         user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> None:
    return service.request_payout(req.paypal_email,
                                  req.amount,
                                  req.scheduled_time,
                                  user)

@router.get("/link", status_code=200)  # Generates a new link
async def get_link(user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> Optional[str]:
    return service.get_newest_link(user)

@router.get("/unpaid-earnings", status_code=200)  # Retrieves unpaid earnings
async def get_unpaid_earnings(user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> float:
    return service.get_unpaid_earnings(user)


@router.get("/statistics", status_code=200)  # Retrieves statistics
async def get_statistics(user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> None:
    statistics =  service.get_statistics(user)

    print(statistics)

    return statistics


@router.get("/payouts/history", status_code=200)  # Retrieves payout history
async def get_payout_history(user: Annotated[Account, Depends(account_service.get_current_active_user)]) -> None:
    return service.get_payout_history(user)