from pydantic import BaseModel
from typing import List, Optional

from datetime import datetime

class PaymentAccount(BaseModel):
    user_id: str | None = None
    subscription_id: str | None = None
    checkout_session_id: str | None = None
    amount: float | None = None
    radom_product_id: str | None = None
    referral_id: Optional[str] = None

class TermsOfService(BaseModel):
    user_id: str | None = None
    date_accepted: datetime | None = None

class Plan(BaseModel):
    name: str | None = None
    tag: str | None = None
    description: Optional[str] = None
    features: List[str] | None = None
    price: float | None = None
    radom_product_id: str | None = None

class CheckoutSessionRequest(BaseModel):
    radom_product_id: str
    referral_id: Optional[str] = None

class CheckoutSessionMetadata(BaseModel):
    checkout_session_id: str
    user_id: str
    referral_id: Optional[str] = None