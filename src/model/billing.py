from pydantic import BaseModel
from typing import List, Optional

from datetime import datetime

class PaymentAccount(BaseModel):
    user_id: str | None = None
    provider: str | None = None
    paypal_plan_id: str | None = None
    paypal_subscription_id: str | None = None
    radom_product_id: str | None = None
    radom_subscription_id: str | None = None
    radom_checkout_session_id: str | None = None
    amount: float | None = None
    gc_billing_request_id: str | None = None
    gc_subscription_id: str | None = None
    gc_mandate_count: int | None = None
    plan_id: str | None = None
    referral_id: Optional[str] = None
    status: str | None = None # disabled, active, payment processsed

# class StripeAccount(BaseModel):
#     user_id: str
#     customer_id: str

class TermsOfService(BaseModel):
    user_id: str | None = None
    date_accepted: datetime | None = None

class Plan(BaseModel):
    plan_id: str
    name: str | None = None
    tag: str | None = None
    description: Optional[str] = None
    features: List[str] | None = None
    price: float | None = None
    # stripe_price_id: str | None = None
    radom_product_id: str | None = None
    paypal_plan_id: str | None = None

class ProductRequest(BaseModel):
    plan_id: str

class RadomCheckoutRequest(BaseModel):
    plan_id: str
    referral_id: Optional[str] = None

class RadomCheckoutSessionMetadata(BaseModel):
    radom_checkout_session_id: str
    user_id: str
    referral_id: Optional[str] = None

class PaypalCheckoutSessionRequest(BaseModel):
    referral_id: Optional[str] = None

class PaypalCheckoutMetadata(BaseModel):
    uuid: str
    user_id: str
    referral_id: Optional[str] = None

class GCRequest(BaseModel):
    plan_id: str
    referral_id: Optional[str] = None