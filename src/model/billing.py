from pydantic import BaseModel
from typing import List, Optional

from datetime import datetime

class PaymentAccount(BaseModel):
    user_id: str | None = None
    stripe_customer_id: str | None = None
    stripe_price_id: str | None = None
    stripe_subscription_id: str | None = None
    paypal_plan_id: str | None = None
    paypal_subscription_id: str | None = None
    radom_product_id: str | None = None
    radom_subscription_id: str | None = None
    radom_checkout_session_id: str | None = None
    amount: float | None = None
    referral_id: Optional[str] = None

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
    stripe_price_id: str | None = None
    radom_product_id: str | None = None
    paypal_plan_id: str | None = None
    paypal_checkout_link: str | None = None

class ProductRequest(BaseModel):
    plan_id: str

class CheckoutSessionRequest(BaseModel):
    plan_id: str
    referral_id: Optional[str] = None

class CheckoutSessionMetadata(BaseModel):
    radom_checkout_session_id: str
    user_id: str
    referral_id: Optional[str] = None

# class StripeItem(BaseModel):
#     data: Optional[dict] = None
#     type: Optional[str] = None

class PaypalCheckoutSessionMetadata(BaseModel):
    paypal_subscription_id: str
    user_id: str
    referral_id: Optional[str] = None