from typing import Optional, List

from datetime import datetime

from model.billing import (PaymentAccount, TermsOfService, Plan,
                           CheckoutSessionMetadata, StripeAccount, 
                           PaypalCheckoutSessionMetadata)

# from .init import payment_account_col, team_col, tos_col, plan_col
from .init import (payment_account_col, tos_col, plan_col, 
                   checkout_session_metadata_col, stripe_account_col, 
                   paypal_checkout_session_metadata_col)

def create_payment_account(user_id: str, 
                           stripe_customer_id: str,
                           stripe_price_id: str,
                           stripe_subscription_id: str,
                           paypal_plan_id: str,
                           paypal_subscription_id: str,
                           radom_subscription_id: str,
                           radom_checkout_session_id: str,
                           amount: float,
                           radom_product_id: str,
                           referral_id: Optional[str] = None) -> None:
    payment_account = payment_account_col.find_one({"user_id": user_id})

    if not payment_account:
        # Create a new payment account
        payment_account = {
            "user_id": user_id,
            "stripe_customer_id": stripe_customer_id,
            "stripe_price_id": stripe_price_id,
            "stripe_subscription_id": stripe_subscription_id,
            "paypal_plan_id": paypal_plan_id,
            "paypal_subscription_id": paypal_subscription_id,
            "radom_subscription_id": radom_subscription_id,
            "radom_checkout_session_id": radom_checkout_session_id,
            "amount": amount,
            "radom_product_id": radom_product_id,
            "referral_id": referral_id
        }
        payment_account_col.insert_one(payment_account)
    else:
        # Update the existing payment account
        update_fields = {
            "stripe_customer_id": stripe_customer_id,
            "stripe_price_id": stripe_price_id,
            "stripe_subscription_id": stripe_subscription_id,
            "paypal_plan_id": paypal_plan_id,
            "paypal_subscription_id": paypal_subscription_id,
            "radom_subscription_id": radom_subscription_id,
            "radom_checkout_session_id": radom_checkout_session_id,
            "amount": amount,
            "radom_product_id": radom_product_id
        }
        
        if referral_id is not None:
            update_fields["referral_id"] = referral_id

        update_fields = {key: value for key, value in update_fields.items() if value is not None}
        
        payment_account_col.update_one(
            {"user_id": user_id},
            {"$set": update_fields}
        )

def remove_payment_account(stripe_subscription_id: Optional[str] = None,
                           paypal_subscription_id: Optional[str] = None,
                           radom_subscription_id: Optional[str] = None) -> None:
    
    # Find the payment account
    payment_account = payment_account_col.find_one({
        "stripe_subscription_id": stripe_subscription_id
        })

    if payment_account:
        payment_account_col.delete_one({
            "stripe_subscription_id": stripe_subscription_id
            })
        return

    # Find the payment account
    payment_account = payment_account_col.find_one({
        "paypal_subscription_id": paypal_subscription_id
        })

    if payment_account:
        payment_account_col.delete_one({
            "paypal_subscription_id": paypal_subscription_id
            })
        return

        
    # Find the payment account
    payment_account = payment_account_col.find_one({
        "radom_subscription_id": radom_subscription_id
    })

    if payment_account:
        payment_account_col.delete_one({
            "radom_subscription_id": radom_subscription_id
        })
        return


def get_payment_account(user_id: str, 
                        stripe_subscription_id: Optional[str] = None,
                        paypal_subscription_id: str = None,
                        radom_checkout_session_id: str = None) -> Optional[PaymentAccount]:
    
    if stripe_subscription_id is not None:
        result = payment_account_col.find_one({
            "stripe_subscription_id": stripe_subscription_id
        })
    elif paypal_subscription_id is not None:
        result = payment_account_col.find_one({
            "paypal_subscription_id": paypal_subscription_id
        })
    elif radom_checkout_session_id is not None:
        result = payment_account_col.find_one({"radom_checkout_session_id": radom_checkout_session_id})
    else:
        result = payment_account_col.find_one({"user_id": user_id})

    if result is not None:
        payment_account = PaymentAccount(**result)
        return payment_account

    return None


def get_stripe_customer_id(user_id: str) -> Optional[str]:
    print("GETTING CUSTOMER ID FROM MONGODB")

    result = payment_account_col.find_one({"user_id": user_id})
    if result is not None:
        print("PARSING RESPONSE TO MODEL")
        return payment_account_col.customer_id
    return None


def accept_tos(user_id: str) -> None:
    # Get the current date and time
    now = datetime.now()


    # Create a new TermsOfService object
    tos = TermsOfService(user_id=user_id, 
                         date_accepted=now)

    result = tos_col.insert_one(tos.dict())

    if not result.inserted_id:
        raise ValueError("Failed to accept Terms of Conditions.")
    

def get_available_plans() -> Optional[List[Plan]]:
    print("GETTING AVAILABLE PLANS")

    results = plan_col.find()

    plans = [Plan(**result) for result in results]

    return plans


def paypal_create_checkout_session_metadata(user_id: str, 
                                            paypal_subscription_id: Optional[str] = None,
                                            referral_id: Optional[str] = None) -> None:
    
    paypal_checkout_session_metadata = paypal_checkout_session_metadata_col.find_one({
        "paypal_subscription_id": paypal_subscription_id
    })

    if not paypal_checkout_session_metadata:
        # Create a new payment account
        paypal_checkout_session_metadata = {
            "user_id": user_id,
            "paypal_subscription_id": paypal_subscription_id,
            "referral_id": referral_id
        }
        paypal_checkout_session_metadata_col.insert_one(paypal_checkout_session_metadata)
    else:
        # Update the existing payment account
        update_fields = {
            "paypal_subscription_id": paypal_subscription_id
        }
        
        if referral_id is not None:
            update_fields["referral_id"] = referral_id

        update_fields = {key: value for key, value in update_fields.items() if value is not None}
        
        payment_account_col.update_one(
            {"user_id": user_id},
            {"$set": update_fields}
        )


def get_paypal_checkout_session_metadata(paypal_subscription_id: Optional[str] = None) -> Optional[CheckoutSessionMetadata]:
    result = checkout_session_metadata_col.find_one({
        "paypal_subscription_id": paypal_subscription_id
    })
    
    # If a result is found, convert it to a Plan instance
    if result:
        return PaypalCheckoutSessionMetadata(**result)
    
    # If no result is found, return None
    return None


def radom_create_checkout_session_metadata(user_id: str, 
                                           radom_checkout_session_id: Optional[str] = None,
                                           referral_id: Optional[str] = None) -> None:
    
    checkout_session_metadata = checkout_session_metadata_col.find_one({"user_id": user_id})

    if not checkout_session_metadata:
        # Create a new payment account
        checkout_session_metadata = {
            "user_id": user_id,
            "radom_checkout_session_id": radom_checkout_session_id,
            "referral_id": referral_id
        }
        checkout_session_metadata_col.insert_one(checkout_session_metadata)
    else:
        # Update the existing payment account
        update_fields = {
            "radom_checkout_session_id": radom_checkout_session_id
        }
        
        if referral_id is not None:
            update_fields["referral_id"] = referral_id

        update_fields = {key: value for key, value in update_fields.items() if value is not None}
        
        payment_account_col.update_one(
            {"user_id": user_id},
            {"$set": update_fields}
        )


def get_radom_checkout_session_metadata(radom_checkout_session_id: Optional[str] = None) -> Optional[CheckoutSessionMetadata]:

    query = {}
    if radom_checkout_session_id:
        query["radom_checkout_session_id"] = radom_checkout_session_id

    result = checkout_session_metadata_col.find_one(query)
    
    # If a result is found, convert it to a Plan instance
    if result:
        return CheckoutSessionMetadata(**result)
    
    # If no result is found, return None
    return None


def get_product(stripe_price_id: Optional[str] = None,
                paypal_plan_id: Optional[str] = None,
                radom_product_id: Optional[str] = None,
                plan_id: Optional[str] = None) -> Optional[Plan]:
    
    query = {}
    if stripe_price_id:
        query = {"stripe_price_id": stripe_price_id}
    elif paypal_plan_id:
        query = {"paypal_plan_id": paypal_plan_id}
    elif radom_product_id:
        query = {"radom_product_id": radom_product_id}
    else:
        query = {"plan_id": plan_id}

    print("GETTING PRODUCT")
    # Query the MongoDB collection based on the non-None field
    result = plan_col.find_one(query)

    print("PRODUCT", result)
    
    # If a result is found, convert it to a Plan instance
    if result:
        return Plan(**result)
    
    # If no result is found, return None
    return None