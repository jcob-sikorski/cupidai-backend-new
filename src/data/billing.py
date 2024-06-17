from typing import Optional, List

from datetime import datetime

from model.account import Account

from model.billing import (PaymentAccount, TermsOfService, Plan,
                           RadomCheckoutSessionMetadata,
                           PaypalCheckoutMetadata)

from .init import (payment_account_col, tos_col, plan_col, 
                   checkout_session_metadata_col,
                   paypal_checkout_metadata_col)

def create_payment_account(user_id: str, 
                           provider: Optional[str] = None,
                           paypal_plan_id: Optional[str] = None,
                           paypal_subscription_id: Optional[str] = None,
                           radom_subscription_id: Optional[str] = None,
                           radom_checkout_session_id: Optional[str] = None,
                           amount: Optional[float] = None,
                           radom_product_id: Optional[str] = None,
                           gc_billing_request_id: Optional[str] = None,
                           gc_subscription_id: Optional[str] = None,
                           gc_mandate_count: Optional[int] = None,
                           plan_id: Optional[str] = None,
                           status: Optional[str] = None,
                           referral_id: Optional[str] = None) -> Optional[PaymentAccount]:
    
    # print("CREATING PAYMENT ACCOUNT")

    payment_account = payment_account_col.find_one({
        "$or": [
            {"user_id": user_id},
            {"gc_billing_request_id": gc_billing_request_id}
        ]
    })

    if not payment_account:
        # print("PAYMENT ACCOUNT NOT FOUND - CREATING NEW ONE...")
        # Create a new payment account
        payment_account = {
            "user_id": user_id,
            "provider": provider,
            "paypal_plan_id": paypal_plan_id,
            "paypal_subscription_id": paypal_subscription_id,
            "radom_subscription_id": radom_subscription_id,
            "radom_checkout_session_id": radom_checkout_session_id,
            "amount": amount,
            "radom_product_id": radom_product_id,
            "gc_billing_request_id": gc_billing_request_id,
            "gc_subscription_id": gc_subscription_id,
            "gc_mandate_count": gc_mandate_count,
            "plan_id": plan_id,
            "status": status,
            "referral_id": referral_id
        }
        print(f"PAYMENT ACCOUNT MODEL FOR INSERT: {payment_account}")
        payment_account_col.insert_one(payment_account)
    else:
        print("PAYMENT ACCOUNT FOUND - UPDATING OLD ONE...")
        # Update the existing payment account
        update_fields = {
            "provider": provider,
            "paypal_plan_id": paypal_plan_id,
            "paypal_subscription_id": paypal_subscription_id,
            "radom_subscription_id": radom_subscription_id,
            "radom_checkout_session_id": radom_checkout_session_id,
            "amount": amount,
            "radom_product_id": radom_product_id,
            "gc_billing_request_id": gc_billing_request_id,
            "gc_subscription_id": gc_subscription_id,
            "plan_id": plan_id,
            "status": status,
        }
        
        if referral_id is not None:
            update_fields["referral_id"] = referral_id

        # Filter out None values
        update_fields = {key: value for key, value in update_fields.items() if value is not None}

        # Prepare the update query
        update_query = {"$set": update_fields}
        
        if gc_mandate_count is not None:
            update_query["$inc"] = {"gc_mandate_count": int(gc_mandate_count)}

        print(f"PAYMENT ACCOUNT MODEL FOR UPDATE: {update_query}")
        
        payment_account_col.update_one(
            {
                "$or": [
                    {"user_id": user_id},
                    {"gc_billing_request_id": gc_billing_request_id}
                ]
            },
            update_query
        )

    if payment_account is not None:
        payment_account = PaymentAccount(**payment_account)

        print(f"FOUND PAYMENT ACCOUNT: {payment_account}")
        return payment_account
    else:
        print("PAYMENT ACCOUNT NOT FOUND")

    return None

def set_payment_account_status(user_id: Optional[str] = None,
                               paypal_subscription_id: Optional[str] = None,
                               radom_subscription_id: Optional[str] = None,
                               gc_billing_request_id: Optional[str] = None,
                               status: Optional[str] = None) -> None:
    print("UPDATING PAYMENT ACCOUNT STATUS...")
    
    # Find the payment account by user_id
    if user_id:
        print("USER ID IS NOT NULL: ", user_id)
        print("LOOKING FOR PAYMENT ACCOUNT...")
        payment_account = payment_account_col.find_one({
            "user_id": user_id
        })
        if payment_account:
            print("FOUND PAYMENT ACCOUNT")
            payment_account_col.update_one(
                {"user_id": user_id},
                {"$set": {"status": status}}
            )
            print("UPDATED PAYMENT ACCOUNT")
            return
        else:
            print("PAYMENT ACCOUNT NOT FOUND")
        
    if paypal_subscription_id:
        print("PAYPAL SUBSCRIPTION ID IS NOT NULL: ", paypal_subscription_id)
        print("LOOKING FOR PAYMENT ACCOUNT...")
        payment_account = payment_account_col.find_one({
            "paypal_subscription_id": paypal_subscription_id
        })
        if payment_account:
            print("FOUND PAYMENT ACCOUNT")
            payment_account_col.update_one(
                {"paypal_subscription_id": paypal_subscription_id},
                {"$set": {"status": status}}
            )
            print("UPDATED PAYMENT ACCOUNT")
            return
        else:
            print("PAYMENT ACCOUNT NOT FOUND")
    
    # Find the payment account by radom_subscription_id
    if radom_subscription_id:
        print("RADOM SUBSCRIPTION ID IS NOT NULL: ", radom_subscription_id)
        print("LOOKING FOR PAYMENT ACCOUNT...")
        payment_account = payment_account_col.find_one({
            "radom_subscription_id": radom_subscription_id
        })
        if payment_account:
            print("FOUND PAYMENT ACCOUNT")
            payment_account_col.update_one(
                {"radom_subscription_id": radom_subscription_id},
                {"$set": {"status": status}}
            )
            print("UPDATED PAYMENT ACCOUNT")
            return
        else:
            print("PAYMENT ACCOUNT NOT FOUND")

    # Find the payment account by gc_billing_request_id
    if gc_billing_request_id:
        print("GC BILLING REQUEST ID IS NOT NULL: ", gc_billing_request_id)
        print("LOOKING FOR PAYMENT ACCOUNT...")
        payment_account = payment_account_col.find_one({
            "gc_billing_request_id": gc_billing_request_id
        })
        if payment_account:
            print("FOUND PAYMENT ACCOUNT")
            payment_account_col.update_one(
                {"gc_billing_request_id": gc_billing_request_id},
                {"$set": {"status": status}}
            )
            print("UPDATED PAYMENT ACCOUNT")
            return
        else:
            print("PAYMENT ACCOUNT NOT FOUND")


def get_payment_account(user_id: str, 
                        paypal_subscription_id: str = None,
                        radom_checkout_session_id: str = None,
                        radom_subscription_id: str = None,
                        gc_billing_request_id: str = None) -> Optional[PaymentAccount]:

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
    elif gc_billing_request_id is not None:
        print("GC BILLING REQUEST ID IS NOT NONE")
        result = payment_account_col.find_one({
            "gc_billing_request_id": gc_billing_request_id
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


def paypal_create_checkout_metadata(referral_id: Optional[str], 
                                    uuid: str,
                                    user_id: str) -> Optional[str]:
    print("CREATING PAYPAL CHECKOUT SESSION")
    result = paypal_checkout_metadata_col.insert_one({
        "user_id": user_id,
        "uuid": uuid,
        "referral_id": referral_id
    })

    if result is not None:
        return uuid
    
    return None


def get_paypal_checkout_metadata(uuid: str) -> Optional[PaypalCheckoutMetadata]:
    print(f"GETTING PAYPAL CHECKOUT METADATA FROM UUID: {uuid}")
    result = paypal_checkout_metadata_col.find_one({
        "uuid": uuid
    })

    # If a result is found, convert it to a Plan instance
    if result:
        print("PAYPAL CHECKOUT METADATA WAS FOUND: ", result)
        return PaypalCheckoutMetadata(**result)
    
    # If no result is found, return None
    print("PAYPAL CHECKOUT METADATA WAS NOT FOUND: ", result)
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
    
    print("CREATING PAYPAL CHECKOUT METADATA...")

    print("LOOKING FOR PAYPAL CHECKOUT SESSION METADATA...")
    paypal_checkout_session_metadata = paypal_checkout_metadata_col.find_one({
        "paypal_subscription_id": paypal_subscription_id
    })

    if not paypal_checkout_session_metadata:
        print("PAYPAL CHECKOUT SESSION METADATA NOT FOUND - CREATING NEW ONE")
        # Create a new payment account
        paypal_checkout_session_metadata = {
            "user_id": user_id,
            "paypal_subscription_id": paypal_subscription_id,
            "referral_id": referral_id
        }
        paypal_checkout_metadata_col.insert_one(paypal_checkout_session_metadata)
    else:
        print("PAYPAL CHECKOUT SESSION METADATA FOUND - UPDATING IT")
        # Update the existing payment account
        update_fields = {
            "paypal_subscription_id": paypal_subscription_id
        }
        
        if referral_id is not None:
            update_fields["referral_id"] = referral_id

        update_fields = {key: value for key, value in update_fields.items() if value is not None}
        
        paypal_checkout_metadata_col.update_one(
            {"user_id": user_id},
            {"$set": update_fields}
        )


def get_paypal_checkout_session_metadata(paypal_subscription_id: Optional[str] = None) -> Optional[RadomCheckoutSessionMetadata]:
    print("GETTING PAYPAL CHECKOUT SESSION METADATA...")
    result = checkout_session_metadata_col.find_one({
        "paypal_subscription_id": paypal_subscription_id
    })
    
    # If a result is found, convert it to a Plan instance
    if result:
        print("PAYPAL CHECKOUT SESSION METADATA FOUND: ", result)
        return PaypalCheckoutMetadata(**result)
    
    print("PAYPAL CHECKOUT SESSION METADATA NOT FOUND: ", result)
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


def get_radom_checkout_session_metadata(radom_checkout_session_id: Optional[str] = None) -> Optional[RadomCheckoutSessionMetadata]:
    print("GETTING RADOM CHECKOUT SESSION METADATA...")
    query = {}
    if radom_checkout_session_id:
        query["radom_checkout_session_id"] = radom_checkout_session_id

    print(f"checkout session metadata query: {query}")

    print("FINDING CHECKOUT SESSION METADATA IN DB...")
    result = checkout_session_metadata_col.find_one(query)
    
    # If a result is found, convert it to a Plan instance
    if result:
        print(f"CHECKOUT SESSION METADATA FOUND: {result}")
        return RadomCheckoutSessionMetadata(**result)
    
    print(f"CHECKOUT SESSION METADATA NOT FOUND: {result}")
    # If no result is found, return None
    return None

def get_product(paypal_plan_id: Optional[str] = None,
                radom_product_id: Optional[str] = None,
                plan_id: Optional[str] = None) -> Optional[Plan]:
    
    print("GETTING PRODUCT...")
    
    query = {}
    if paypal_plan_id:
        print("PAYPAL PLAN ID IS NOT NULL: ", paypal_plan_id)
        query = {"paypal_plan_id": paypal_plan_id}
    elif radom_product_id:
        print("RADOM PRODUCT ID IS NOT NULL: ", radom_product_id)
        query = {"radom_product_id": radom_product_id}
    else:
        print("PLAN ID IS NOT NULL: ", plan_id)
        query = {"plan_id": plan_id}

    print("LOOKING FOR RADOM PRODUCT/PAYPAL PLAN...")
    # Query the MongoDB collection based on the non-None field
    result = plan_col.find_one(query)
    
    # If a result is found, convert it to a Plan instance
    if result:
        print("RADOM PRODUCT/PAYPAL PLAN FOUND: ", result)
        return Plan(**result)
    
    print("RADOM PRODUCT/PAYPAL PLAN NOT FOUND: ", result)
    # If no result is found, return None
    return None