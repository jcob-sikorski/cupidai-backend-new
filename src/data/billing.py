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
                           referral_id: Optional[str] = None) -> None:

    payment_account = payment_account_col.find_one({"user_id": user_id})

    if not payment_account:
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
        payment_account_col.insert_one(payment_account)
    else:
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
        
        payment_account_col.update_one(
            {"user_id": user_id},
            {"$set": update_fields}
        )

def remove_payment_account(user_id: Optional[str] = None,
                           radom_subscription_id: Optional[str] = None) -> None:
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

    print("\n\ngetting payment account...")

    print(f"get_payment_account args: user_id: {user_id}, paypal_subscription_id: {paypal_subscription_id}, radom_checkout_session_id: {radom_checkout_session_id}")

    if paypal_subscription_id is not None:
        result = payment_account_col.find_one({
            "paypal_subscription_id": paypal_subscription_id
        })
    elif radom_checkout_session_id is not None:
        result = payment_account_col.find_one({
            "radom_checkout_session_id": radom_checkout_session_id
        })
    elif radom_subscription_id is not None:
        result = payment_account_col.find_one({
            "radom_subscription_id": radom_subscription_id
        })
    else:
        result = payment_account_col.find_one({
            "user_id": user_id
        })

    if result is not None:
        payment_account = PaymentAccount(**result)

        print(f"got payment_account: {payment_account}")
        return payment_account

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
    
    print(f"metadata values: user_id: {user_id}, radom_checkout_session_id: {radom_checkout_session_id}, referral_id: {referral_id}")
    checkout_session_metadata = checkout_session_metadata_col.find_one({"user_id": user_id})

    if not checkout_session_metadata:
        print("user not found - creating new radom checkout session metadata")
        # Create a new payment account
        checkout_session_metadata = {
            "user_id": user_id,
            "radom_checkout_session_id": radom_checkout_session_id,
            "referral_id": referral_id
        }
        checkout_session_metadata_col.insert_one(checkout_session_metadata)
    else:
        print("user found - updating radom checkout session id")
        # Update the existing payment account
        update_fields = {
            "radom_checkout_session_id": radom_checkout_session_id
        }
        
        print("checking if referral id is not None")
        if referral_id is not None:
            print(f"referral_id is not None: {referral_id}")
            print("adding refferal_id to the radom checkout session metadata")
            update_fields["referral_id"] = referral_id
        else:
            print(f"referral_id is None: {referral_id}")

        update_fields = {key: value for key, value in update_fields.items() if value is not None}

        print(f"update fields for checkout session metadata: {update_fields}")
        
        payment_account_col.update_one(
            {"user_id": user_id},
            {"$set": update_fields}
        )
        print("radom checkout session metadata has been updared updated")


def get_radom_checkout_session_metadata(radom_checkout_session_id: Optional[str] = None) -> Optional[CheckoutSessionMetadata]:
    print("\n\ngetting radom checkout session metadata...")
    query = {}
    if radom_checkout_session_id:
        query["radom_checkout_session_id"] = radom_checkout_session_id

    print(f"radom_checkout_session_id: {radom_checkout_session_id}")
    print(f"checkout session metadata query: {query}")

    print("finding result in db...")
    result = checkout_session_metadata_col.find_one(query)

    print(f"got result: {result}")
    
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