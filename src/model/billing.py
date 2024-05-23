from pydantic import BaseModel
from typing import List, Optional

from datetime import datetime

class PaymentAccount(BaseModel):
    user_id: str | None = None
    radom_subscription_id: str | None = None
    radom_checkout_session_id: str | None = None
    amount: float | None = None
    radom_product_id: str | None = None
    referral_id: Optional[str] = None

class TermsOfService(BaseModel):
    user_id: str | None = None
    date_accepted: datetime | None = None

# TODO: this should have a paypal product id and link to the checkout
class Plan(BaseModel):
    name: str | None = None
    tag: str | None = None
    description: Optional[str] = None
    features: List[str] | None = None
    price: float | None = None
    radom_product_id: str | None = None
    stripe_product_id: str | None = None

class ProductRequest(BaseModel):
    paypal_product_id: Optional[str] = None
    radom_product_id: Optional[str] = None

class CheckoutSessionRequest(BaseModel):
    radom_product_id: str
    referral_id: Optional[str] = None

class CheckoutSessionMetadata(BaseModel):
    radom_checkout_session_id: str
    user_id: str
    referral_id: Optional[str] = None