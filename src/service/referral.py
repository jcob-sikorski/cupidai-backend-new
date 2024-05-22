from fastapi import HTTPException

from typing import Optional

from data import referral as data

from model.account import Account
from model.referral import PayoutSubmission, Referral

def generate_link(user: Account) -> str:
    return data.generate_link(user.user_id)

def link_clicked(referral_id: str) -> None:
    print("LINK CLICKED")
    try:
        referral = get_referral(referral_id)

        print(f"REFERRAL: {referral.dict()}")
        update_statistics(referral.host_id, amount=0, clicked=True, signup_ref=False)
    except ValueError:
        raise ValueError(f"Referral with ID {referral_id} does not exist.")

def remove_link(user: Account) -> None:
    return data.remove_link(user.user_id)

def request_payout(paypal_email: str,
                   amount: float,
                   scheduled_time: str,
                   user: Account) -> None:
    try:
        data.request_payout(paypal_email,
                            amount,
                            scheduled_time,
                            user.user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Payout not available.")
    
def get_newest_link(user: Account) -> Optional[str]:
    return data.get_newest_link(user.user_id)

def get_unpaid_earnings(user: Account) -> float:
    return data.get_unpaid_earnings(user.user_id)

def get_referral(referral_id: str) -> Optional[Referral]:
    return data.get_referral(referral_id)

def update_statistics(user_id: str, amount: float, clicked: bool, signup_ref: bool):
    return data.update_statistics(user_id, amount, clicked, signup_ref)

def log_signup_ref(referral_id: str,
                 user: Account) -> None:
    print("LOGGING REFERRAL")
    try:
        data.add_link_user(referral_id, user.user_id)

        referral = get_referral(referral_id)

        print(f"REFERRAL: {referral.dict()}")
        update_statistics(referral.host_id, amount=0, clicked=False, signup_ref=True)
    except ValueError:
        raise ValueError(f"Referral with ID {referral_id} does not exist.")

def get_statistics(user: Account) -> None:
    return data.get_statistics(user.user_id)

def get_payout_history(user: Account) -> None:
    return data.get_payout_history(user.user_id)