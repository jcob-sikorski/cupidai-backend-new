from typing import Optional, List

from model.referral import Referral, Earnings, Statistics, PayoutSubmission, PayoutHistory

from .init import referral_col, payout_submission_col, earnings_col, statistics_col, payout_history_col

from pymongo import DESCENDING

from uuid import uuid4

from datetime import datetime, timedelta

def generate_link(user_id: str) -> str:
    referral_id = str(uuid4())

    referral = Referral(
        referral_id=referral_id,
        host_id=user_id,
        guest_ids=[]
    )

    referral_col.insert_one(referral.dict())

    return referral_id

def remove_link(referral_id: str) -> None:
    referral_col.delete_one({"referral_id": referral_id})

def add_link_user(referral_id: str,
                    user_id: str) -> None:
    print("ADDING LINK USER")

    result = referral_col.update_one(
        {"referral_id": referral_id},
        {
            "$addToSet": {"guest_ids": user_id}
        }
    )
    if result.modified_count == 0:
        raise ValueError(f"Referral with ID {referral_id} does not exist.")

def request_payout(paypal_email: str,
                   amount: float,
                   scheduled_time: str,
                   user_id: str) -> None:
    earnings = earnings_col.find_one({"user_id": user_id})

    if earnings is None or earnings.get('amount', 0) <= amount:
        raise ValueError("Payout not available.")
    
    payout_submission = PayoutSubmission(
        user_id=user_id,
        paypal_email=paypal_email,
        amount=amount,
        scheduled_time=scheduled_time,
        date=datetime.now()
    )

    payout_submission_col.insert_one(payout_submission.dict())

def get_newest_link(user_id: str) -> Optional[str]:
    referral = referral_col.find_one({"host_id": user_id})

    print(referral)

    if referral:
        return referral["referral_id"]

    return None

def get_unpaid_earnings(user_id: str) -> float:
    earnings = earnings_col.find_one({"user_id": user_id})

    if earnings and earnings['amount'] > 0:
        return earnings['amount']

    return 0.00

def get_referral(referral_id: str) -> Optional[Referral]:
    referral = referral_col.find_one({"referral_id": referral_id})

    if referral:
        return Referral(**referral)

    return None

def update_statistics(user_id: str, amount_bought: float, clicked: bool, signup_ref: bool):
    print("UPDATIG STATISTICS")
    now = datetime.now()
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)  # Monday at midnight
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)  # First day of the month at midnight
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)  # First day of the year at midnight

    periods = {
        "weekly": week_start,
        "monthly": month_start,
        "yearly": year_start
    }

    print(f"PERIODS: {periods}")

    if clicked:
        for period, start_date in periods.items():
            updates = {
                '$inc': {
                    'referral_link_clicks': 1
                }
            }
            statistics_col.find_one_and_update(
                {"user_id": user_id, "period": period, "period_date": start_date},
                updates,
                upsert=True
            )
            
    else:
        for period, start_date in periods.items():
            updates = {
                '$inc': {
                    'purchases_made': 1, 'earned': amount_bought * 0.4
                } if not signup_ref else {
                    'referral_link_signups': 1
                }
            }

            statistics_col.find_one_and_update(
                {"user_id": user_id, "period": period, "period_date": start_date},
                updates,
                upsert=True
            )

            updates = {
                '$inc': {
                    'amount': amount_bought * 0.4
                }
            }

            earnings_col.find_one_and_update(
                {"user_id": user_id},
                updates,
                upsert=True
            )

def get_statistics(user_id: str) -> List[Statistics]:
    # Group the sorted results by period and select the document with the maximum period_value within each group
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$sort": {"period_value": DESCENDING}},
        {"$group": {"_id": "$period", "latest_statistic": {"$first": "$$ROOT"}}}
    ]

    aggregated_results = statistics_col.aggregate(pipeline)

    # Convert the aggregated results to Statistics objects
    statistics = [Statistics(**result["latest_statistic"]) for result in aggregated_results]

    # If no statistics found, create default Statistics objects for each period type
    if not statistics:
        statistics = [
            Statistics(period="weekly", 
                       period_value=0, 
                       referral_link_clicks=0, 
                       referral_link_signups=0, 
                       purchases_made=0, 
                       earned=0, 
                       user_id=user_id),

            Statistics(period="monthly", 
                       period_value=0, 
                       referral_link_clicks=0, 
                       purchases_made=0, 
                       earned=0, 
                       user_id=user_id),

            Statistics(period="yearly", 
                       period_value=0, 
                       referral_link_clicks=0, 
                       purchases_made=0, 
                       earned=0, 
                       user_id=user_id)
        ]

    return statistics


def get_payout_history(user_id: str) -> None:
    payout_history = payout_history_col.find_one({"user_id": user_id})

    if payout_history:
        return PayoutHistory(**payout_history)

    return None