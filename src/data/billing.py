from typing import Optional, List

from datetime import datetime

from model.account import Account

from model.billing import (PaymentAccount, TermsOfService, Plan,
                           CheckoutSessionMetadata,
                           PaypalCheckoutSessionMetadata)

from .init import (payment_account_col, tos_col, plan_col, 
                   checkout_session_metadata_col,
                   paypal_checkout_session_metadata_col,
                   paypal_uuid_col)

def create_payment_account(user_id: str, 
                           paypal_plan_id: Optional[str] = None,
                           paypal_subscription_id: Optional[str] = None,
                           radom_subscription_id: Optional[str] = None,
                           radom_checkout_session_id: Optional[str] = None,
                           amount: Optional[float] = None,
                           radom_product_id: Optional[str] = None,
                           referral_id: Optional[str] = None) -> Optional[PaymentAccount]:
    
    print("CREATING PAYMENT ACCOUNT")

    payment_account = payment_account_col.find_one({"user_id": user_id})

    if not payment_account:
        print("PAYMENT ACCOUNT NOT FOUND - CREATING NEW ONE...")
        # Create a new payment account
        payment_account = {
            "user_id": user_id,
            "paypal_plan_id": paypal_plan_id,
            "paypal_subscription_id": paypal_subscription_id,
            "radom_subscription_id": radom_subscription_id,
            "radom_checkout_session_id": radom_checkout_session_id,
            "amount": amount,
            "radom_product_id": radom_product_id,
            "referral_id": referral_id
        }
        print(f"PAYMENT ACCOUNT MODEL FOR INSERT: {payment_account}")
        payment_account_col.insert_one(payment_account)
    else:
        print("PAYMENT ACCOUNT FOUND - UPDATING OLD ONE...")
        # Update the existing payment account
        update_fields = {
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

        print(f"PAYMENT ACCOUNT MODEL FOR UPDATE: {update_fields}")
        
        payment_account_col.update_one(
            {"user_id": user_id},
            {"$set": update_fields}
        )

    if payment_account is not None:
        payment_account = PaymentAccount(**payment_account)

        print(f"FOUND PAYMENT ACCOUNT: {payment_account}")
        return payment_account
    else:
        print("PAYMENT ACCOUNT NOT FOUND")

    return None

def remove_payment_account(user_id: Optional[str] = None,
                           radom_subscription_id: Optional[str] = None) -> None:
    print("REMOVING PAYMENT ACCOUNT...")
    
    # Find the payment account
    payment_account = payment_account_col.find_one({
        "user_id": user_id
        })

    if payment_account:
        payment_account_col.delete_one({
            "user_id": user_id
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
                        paypal_subscription_id: str = None,
                        radom_checkout_session_id: str = None,
                        radom_subscription_id: str = None) -> Optional[PaymentAccount]:

    print("GETTING PAYMENT ACCOUNT...")

    if paypal_subscription_id is not None:
        print("PAYPAL SUBSCRIPTION ID IS NOT NONE")
        result = payment_account_col.find_one({
            "paypal_subscription_id": paypal_subscription_id
        })
    elif radom_checkout_session_id is not None:
        print("RADOM CHECKOUT SESSION ID IS NOT NONE")
        result = payment_account_col.find_one({
            "radom_checkout_session_id": radom_checkout_session_id
        })
    elif radom_subscription_id is not None:
        print("RADOM SUBSCRIPTION ID IS NOT NONE")
        result = payment_account_col.find_one({
            "radom_subscription_id": radom_subscription_id
        })
    else:
        print("USER ID IS NOT NONE")
        result = payment_account_col.find_one({
            "user_id": user_id
        })

    if result is not None:
        payment_account = PaymentAccount(**result)

        print(f"FOUND PAYMENT ACCOUNT: {payment_account}")
        return payment_account
    else:
        print("PAYMENT ACCOUNT NOT FOUND")

    return None


def paypal_obtain_uuid(user_id: str,
                       uuid: str) -> Optional[str]:
    result = paypal_uuid_col.insert_one({
        "user_id": user_id,
        "uuid": uuid
    })

    if result is not None:
        return uuid
    
    return None


def get_paypal_user_id_from_uuid(uuid: str) -> Optional[str]:
    result = paypal_uuid_col.find_one({
        "uuid": uuid
    })

    if result is not None:
        return result.get('user_id')
    
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
    
    print("CREATING RADOM CHECKOUT SESSION METADATA...")
    
    checkout_session_metadata = checkout_session_metadata_col.find_one({"user_id": user_id})

    if not checkout_session_metadata:
        print("RADOM CHECKOUT SESSION METADATA NOT FOUND")
        print("CREATING NEW CHECKOUT SESSOIN METADATA: ")
        # Create a new payment account
        checkout_session_metadata = {
            "user_id": user_id,
            "radom_checkout_session_id": radom_checkout_session_id,
            "referral_id": referral_id
        }
        print(checkout_session_metadata)
        checkout_session_metadata_col.insert_one(checkout_session_metadata)
    else:
        print("RADOM CHECKOUT SESSION METADATA FOUND")

        print("UPDATING CHECKOUT SESSOIN METADATA: ")
        # Update the existing payment account
        update_fields = {
            "radom_checkout_session_id": radom_checkout_session_id,
            "referral_id": referral_id
        }

        update_fields = {key: value for key, value in update_fields.items() if value is not None}

        print(f"UPDATING FIELDS FOR CHECKOUT SESSION METADATA: {update_fields}")
        
        checkout_session_metadata_col.update_one(
            {"user_id": user_id},
            {"$set": update_fields}
        )


def get_radom_checkout_session_metadata(radom_checkout_session_id: Optional[str] = None) -> Optional[CheckoutSessionMetadata]:
    print("GETTING RADOM CHECKOUT SESSION METADATA...")
    query = {}
    if radom_checkout_session_id:
        query["radom_checkout_session_id"] = radom_checkout_session_id

    print(f"checkout session metadata query: {query}")

    print("FINDING CHECKOUT SESSION METADATA IN DB...")
    result = checkout_session_metadata_col.find_one(query)

    print(f"GOT CHECKOUT SESSION METADATA: {result}")
    
    # If a result is found, convert it to a Plan instance
    if result:
        return CheckoutSessionMetadata(**result)
    
    # If no result is found, return None
    return None

def get_product(paypal_plan_id: Optional[str] = None,
                radom_product_id: Optional[str] = None,
                plan_id: Optional[str] = None) -> Optional[Plan]:
    
    query = {}
    if paypal_plan_id:
        query = {"paypal_plan_id": paypal_plan_id}
    elif radom_product_id:
        query = {"radom_product_id": radom_product_id}
    else:
        query = {"plan_id": plan_id}

    # Query the MongoDB collection based on the non-None field
    result = plan_col.find_one(query)
    
    # If a result is found, convert it to a Plan instance
    if result:
        return Plan(**result)
    
    # If no result is found, return None
    return None