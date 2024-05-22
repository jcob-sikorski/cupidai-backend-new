from pydantic import BaseModel
from typing import List

from datetime import datetime

class PayoutSubmission(BaseModel):
    user_id: str | None = None
    # withdrawal_method: str | None = None
    paypal_email: str | None = None
    amount: float | None = None
    scheduled_time: str | None = None
    # team_notes: str
    date: datetime | None = None

class PayoutHistory(BaseModel):
    date: str | None = None
    payment_id: str | None = None
    user_id: str | None = None
    amount: float | None = None
    status: str | None = None

class Earnings(BaseModel):
    user_id: str | None = None
    amount: float | None = None

class Statistics(BaseModel):
    period: str | None = None  # This can be 'weekly', 'monthly', or 'yearly'
    referral_link_clicks: int | None = None
    referral_link_signups: int | None = None
    purchases_made: int | None = None
    earned: float | None = None
    user_id: str | None = None

# this is for a single generated link
# its idea is to securely map a link to the user_id
class Referral(BaseModel):
    referral_id: str | None = None
    host_id: str | None = None
    guest_ids: List[str] | None = None