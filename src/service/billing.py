from fastapi import Request, HTTPException

from typing import Optional, Dict, Any

import os

import requests

import json

from uuid import uuid4

import base64

import data.billing as data

from model.account import Account

from model.billing import (Plan, CheckoutSessionRequest, 
                           CheckoutSessionMetadata, PaymentAccount)

import service.account as account_service

import service.referral as referral_service

def has_permissions(feature: str, 
                    user: Account) -> bool:
    
    if account_service.is_insider(user):
        return True

    plan = get_current_plan(user)

    if plan and feature in plan.features:
        return True
            
    return False

def create_radom_checkout_session(
    req: CheckoutSessionRequest,
    user: Account
) -> Dict[str, Any]:
    payment_account = get_payment_account(user.user_id)

    if payment_account:
        raise HTTPException(
            status_code=403,
            detail="You have to first cancel your plan to create a new one."
        )
    
    url = "https://api.radom.com/checkout_session"
    
    product = get_product(plan_id=req.plan_id)

    payload = {
        "lineItems": [
            {
                "productId": product.radom_product_id,
                "itemData": {
                    "name": product.name,
                    "description": product.description,
                    "chargingIntervalSeconds": 3600 * 24 * 30,
                    "price": product.price,
                    "isMetered": False,
                    "currency": "GBP",
                    "sendSubscriptionEmails": True
                }
            }
        ],
        "currency": "GBP",
        "gateway": {
            "managed": {
                "methods": [
                    {
                        "network": "Bitcoin",
                        "discountPercentOff": 0
                    },
                    {
                        "network": "Ethereum",
                        "discountPercentOff": 0
                    },
                    {
                        "network": "Ethereum",
                        "token": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                        "discountPercentOff": 0
                    },
                    {
                        "network": "Ethereum",
                        "token": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                        "discountPercentOff": 0
                    }
                ]
            }
        },
        "successUrl": f"{os.getenv('WEBAPP_DOMAIN')}/dashboard",
        "cancelUrl": f"{os.getenv('WEBAPP_DOMAIN')}/dashboard",
        "metadata": [
            {
                "key": "user_id",
                "value": user.user_id
            }
        ],
        "expiresAt": 1747827000,
        "customizations": {
            "leftPanelColor": "#FFFFFF",
            "primaryButtonColor": "#000000",
            "slantedEdge": True,
            "allowDiscountCodes": False
        },
        "chargeCustomerNetworkFee": True
    }

    if os.getenv('MODE') == 'development' or os.getenv('MODE') == 'staging':
        payload["gateway"]["managed"]["methods"].append({
            "network": "SepoliaTestnet",
            "token": "0xa4fCE8264370437e718aE207805b4e6233638b9E",
            "discountPercentOff": 0
        })

    headers = {
        "Content-Type": "application/json",
        "Authorization": os.getenv('RADOM_ACCESS_TOKEN')
    }

    print("\n\ncreating radom checkout session...")
    try:
        response = requests.request("POST", url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for any HTTP error
        response_data = response.json()
        print(f"response from radom: {response_data}\n")
        
        radom_checkout_session_id = response_data.get('checkoutSessionId')
        
        if radom_checkout_session_id:
            print("checkout session id is not null")
            radom_create_checkout_session_metadata(user.user_id,
                                                   radom_checkout_session_id,
                                                   req.referral_id)
        
        return response_data
    except requests.exceptions.RequestException as e:
        print("Error creating checkout session:", e)
        return {}  # Return an empty dictionary in case of error


async def radom_webhook(request: Request) -> None:
    body = await request.body()
    body_str = body.decode()

    # Parse JSON string into a Python dictionary
    body_dict = json.loads(body_str)

    print(f"radom request body: {body_dict}")

    # Extract the event type
    event_type = body_dict.get("eventType")

    if event_type == "newSubscription":
        print("event type is new subscription")

        print("getting radom_subscription_id...")
        radom_subscription_id = body_dict.get("eventData", {})          \
                                         .get("newSubscription", {})    \
                                         .get("subscriptionId")
        
        print(f"got radom_subscription_id: {radom_subscription_id}")

        print("getting radom_checkout_session_id...")
        radom_checkout_session_id = body_dict.get("radomData", {})          \
                                             .get("checkoutSession", {})    \
                                             .get("checkoutSessionId")
        
        print(f"got radom_checkout_session_id: {radom_checkout_session_id}")

        print("getting amount...")
        amount = body_dict.get("eventData", {})         \
                          .get("newSubscription", {})   \
                          .get("amount", {})
        
        print(f"got amount: {amount}")


        print("getting radom_product_id...")
        radom_product_id = body_dict.get("eventData", {})           \
                                    .get("newSubscription", {})     \
                                    .get("tags", {})                \
                                    .get("productId")
        
        print(f"got radom_product_id: {radom_product_id}")

        print("getting metadata...")
        metadata = body_dict.get("radomData", {})           \
                            .get("checkoutSession", {})     \
                            .get("metadata", [])
        
        print(f"got metadata: {metadata}")

        print("trying to find user id in metadata...")
        user_id = None
        for item in metadata:
            if item.get("key") == "user_id":
                print(f"found user id in metadata: {user_id}")
                user_id = item.get("value")

        if not user_id:
            print(f"user_id is None: {user_id}")

        internal_metadata = get_radom_checkout_session_metadata(radom_checkout_session_id)

        print(f"got radom checkout session metadata: {internal_metadata}")

        referral_id = internal_metadata.referral_id if internal_metadata else None

        print(f"got referral_id from metadata: {referral_id}")

        create_payment_account(user_id=user_id, 
                               paypal_plan_id=None,
                               paypal_subscription_id=None,
                               radom_subscription_id=radom_subscription_id, 
                               radom_checkout_session_id=radom_checkout_session_id, 
                               amount=amount,
                               radom_product_id=radom_product_id,
                               referral_id=referral_id)

    elif event_type == "paymentTransactionConfirmed":
        print("event type is payment transaction confirmed")

        print("getting radom checkout session id...")
        radom_checkout_session_id = body_dict.get("radomData", {})          \
                                              .get("checkoutSession", {})   \
                                              .get("checkoutSessionId")

        print(f"got radom_checkout_session_id: {radom_checkout_session_id}")

        payment_account = get_payment_account(user_id='',
                                              radom_checkout_session_id=radom_checkout_session_id)
        
        print("checking if payment account has referral id...")
        if payment_account and payment_account.referral_id:
            print(f"payment account has referral id: {payment_account.referral_id}")
            referral = referral_service.get_referral(payment_account.referral_id)

            print(f"got referral: {referral}")

            referral_service.update_for_host(referral,
                                             amount)

    elif event_type == "subscriptionExpired":
        radom_subscription_id = body_dict.get("eventData", {}).get("newSubscription", {}).get("subscriptionId")

        remove_payment_account(radom_subscription_id=radom_subscription_id)
    elif event_type == "subscriptionCancelled":
        radom_subscription_id = body_dict.get("eventData", {}).get("subscriptionCancelled", {}).get("subscriptionId")

        payment_account = get_payment_account(user_id='',
                                              radom_checkout_session_id=radom_checkout_session_id)
        
        print("checking if payment account has referral id...")
        if payment_account and payment_account.referral_id:
            print(f"payment account has referral id: {payment_account.referral_id}")
            referral = referral_service.get_referral(payment_account.referral_id)

            print(f"got referral: {referral}")

            referral_service.update_for_host(referral,
                                             amount)

        # remove_payment_account(radom_subscription_id=radom_subscription_id)

    return

async def paypal_webhook(request: Request) -> None:
    # Read the request body
    body = await request.body()
        
    # Decode the body content to a string
    body_str = body.decode("utf-8")

    # Parse the JSON string into a dictionary
    body_dict = dict(json.loads(body_str))

    event_type = body_dict.get('event_type')
    
    if event_type is None:
        raise HTTPException(status_code=400, detail="Event type not found in request")

    # Handle subscription events
    elif event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
        paypal_subscription_id = body_dict.get("resource", {}) \
                                          .get("id", {})
        
        amount = body_dict.get("resource", {})     \
                          .get("billing_info", {}) \
                          .get("last_payment", {}) \
                          .get("amount", {})       \
                          .get("value", {})
        
        paypal_plan_id = body_dict.get("resource", {}) \
                                  .get("plan_id", {})
        
        custom_id = body_dict.get("resource", {}) \
                              .get("custom_id", {})
        
        user_id = get_paypal_user_id_from_uuid(custom_id)

        create_payment_account(user_id=user_id,
                               paypal_plan_id=paypal_plan_id,
                               paypal_subscription_id=paypal_subscription_id,
                               radom_subscription_id=None, 
                               radom_checkout_session_id=None, 
                               amount=amount,
                               radom_product_id=None,
                               referral_id=None)

    # Handle subscription events
    elif event_type == "PAYMENT.SALE.REFUNDED" or event_type == "PAYMENT.SALE.REVERSED" or \
         event_type == "PAYMENT.SALE.DENIED" or event_type == "BILLING.SUBSCRIPTION.CANCELLED":

        custom_id = body_dict.get("resource", {}) \
                              .get("custom", {})
        
        user_id = get_paypal_user_id_from_uuid(custom_id)

        remove_payment_account(user_id=user_id)
    else:
        print("Unhandled event type:", event_type)
    
    return {"status": "success"}

def paypal_obtain_uuid(user: Account) -> Optional[str]:
    uuid = str(uuid4())
    return data.paypal_obtain_uuid(user.user_id,
                                   uuid)
def get_paypal_user_id_from_uuid(uuid: str) -> Optional[Account]:
    return data.get_paypal_user_id_from_uuid(uuid)

def get_paypal_access_token():
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET")

    # Encode CLIENT_ID:CLIENT_SECRET in Base64
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    # Set up the headers and data for the request
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type': 'client_credentials'
    }

    # Make the POST request
    response = requests.post(f"{os.getenv('PAYPAL_DOMAIN')}/oauth2/token", headers=headers, data=data)

    # Check the response
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print("Error getting access token:", response.status_code, response.json())



def fetch_subscription_details(subscription_id: str, access_token: str):
    url = f"{os.getenv('PAYPAL_DOMAIN')}/billing/subscriptions/{subscription_id}"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(url, headers=headers)
    return response


def cancel_plan(user: Account) -> bool:
    access_token = get_paypal_access_token()

    payment_account = get_payment_account(user.user_id)

    payment_account = get_payment_account(user.user_id)
    if payment_account and hasattr(payment_account, 'paypal_subscription_id') \
       and payment_account.paypal_subscription_id is not None \
       and len(payment_account.paypal_subscription_id) > 0:
        subscription_id = payment_account.paypal_subscription_id

        access_token = get_paypal_access_token()

        if access_token is None:
            print("Failed to obtain access token.")
            return False

        # Fetch subscription details to verify existence
        details_response = fetch_subscription_details(subscription_id, access_token)
        if details_response.status_code != 200:
            print(f'Failed to fetch subscription details for {subscription_id}. Response: {details_response.text}')
            return False

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}',
        }

        data = {
            "reason": ""
        }

        url = f"{os.getenv('PAYPAL_DOMAIN')}/billing/subscriptions/{subscription_id}/cancel"

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 204:
            print(f'Subscription {subscription_id} cancelled successfully.')
            return True
        else:
            print(f'Failed to cancel subscription {subscription_id}. Response: {response.text}')
            return False
        
    elif payment_account and hasattr(payment_account, 'radom_subscription_id') \
         and payment_account.radom_subscription_id is not None \
         and len(payment_account.radom_subscription_id) > 0:
        url = f"https://api.radom.com/subscription/{payment_account.radom_subscription_id}/cancel"

        headers = {
            "Content-Type": "application/json",
            "Authorization": os.getenv('RADOM_ACCESS_TOKEN')
        }

        response = requests.request("POST", url, headers=headers)

        if response.status_code == 200:
            return True

    return False

    # TODO: implement paypal too


def get_available_plans(user: Account) -> Optional[Dict[str, Any]]:
    # Retrieve available plans
    plans = data.get_available_plans()
    
    # Get the current plan for the user
    current_plan = get_current_plan(user)
    
    # Return the result as a dictionary
    return {
        "plans": plans,
        "active_plan_id": current_plan.plan_id if current_plan else None
    }


def radom_create_checkout_session_metadata(user_id: str, 
                                           radom_checkout_session_id: Optional[str] = None,
                                           referral_id: Optional[str] = None) -> None:
    print("creating radom checkout session metadata")
    return data.radom_create_checkout_session_metadata(user_id=user_id, 
                                                       radom_checkout_session_id=radom_checkout_session_id,
                                                       referral_id=referral_id)
    

def get_radom_checkout_session_metadata(radom_checkout_session_id: Optional[str] = None) -> Optional[CheckoutSessionMetadata]:
    return data.get_radom_checkout_session_metadata(radom_checkout_session_id)


def get_product(paypal_plan_id: Optional[str] = None,
                radom_product_id: Optional[str] = None,
                plan_id: Optional[str] = None) -> Optional[Plan]:
    return data.get_product(paypal_plan_id, 
                            radom_product_id,
                            plan_id)

def create_payment_account(user_id: str, 
                           paypal_plan_id: str,
                           paypal_subscription_id: str,
                           radom_subscription_id: str,
                           radom_checkout_session_id: str,
                           amount: float,
                           radom_product_id: str,
                           referral_id: Optional[str] = None):
    
    return data.create_payment_account(user_id, 
                                       paypal_plan_id,
                                       paypal_subscription_id,
                                       radom_subscription_id,
                                       radom_checkout_session_id,
                                       amount,
                                       radom_product_id,
                                       referral_id)


def remove_payment_account(user_id: Optional[str] = None,
                           radom_subscription_id: Optional[str] = None) -> None:
    return data.remove_payment_account(user_id,
                                       radom_subscription_id)


def get_payment_account(user_id: str, 
                        paypal_subscription_id: str = None,
                        radom_checkout_session_id: str = None,
                        radom_subscription_id: str = None) -> Optional[PaymentAccount]:
    
    return data.get_payment_account(user_id,
                                    paypal_subscription_id,
                                    radom_checkout_session_id,
                                    radom_subscription_id)


def get_current_plan(user: Account) -> Optional[Plan]:
    payment_account = get_payment_account(user.user_id)

    if payment_account:
        return get_product(paypal_plan_id=payment_account.paypal_plan_id,
                           radom_product_id=payment_account.radom_product_id)
