from fastapi import Request, HTTPException

from typing import Optional, Dict, Any

import os

import requests

import json

import data.billing as data

from model.account import Account
from model.billing import (Plan, CheckoutSessionRequest, 
                           CheckoutSessionMetadata, PaymentAccount)

import service.account as account_service
import service.email as email_service
import service.referral as referral_service


def has_permissions(feature: str, 
                    user: Account) -> bool:
    
    payment_account = get_payment_account(user.user_id)

    if payment_account and payment_account.subscription_id:
        url = f"https://api.radom.com/subscription/{payment_account.subscription_id}"

        headers = {
            "Content-Type": "application/json",
            "Authorization": os.getenv("RADOM_ACCESS_TOKEN")
        }

        response = requests.request("GET", url, headers=headers)

        response_json = response.json()

        status = response_json.get("status", {})

        if status == "active":
            plan = get_current_plan(user)

            if plan and feature in plan.features:
                return True
            
    return False

def create_checkout_session(
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
    
    product = get_product(req.radom_product_id)

    print(product)

    print(req.radom_product_id)

    print(os.getenv('WEBAPP_DOMAIN'))

    print(user.user_id)

    print(req.referral_id)

    print(os.getenv('RADOM_ACCESS_TOKEN'))

    payload = {
        "lineItems": [
            {
                "productId": req.radom_product_id,
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

    if os.getenv('MODE') == 'staging':
        payload["gateway"]["managed"]["methods"].append({
            "network": "SepoliaTestnet",
            "token": "0xa4fCE8264370437e718aE207805b4e6233638b9E",
            "discountPercentOff": 0
        })

    headers = {
        "Content-Type": "application/json",
        "Authorization": os.getenv('RADOM_ACCESS_TOKEN')
    }

    try:
        response = requests.request("POST", url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for any HTTP error
        response_data = response.json()
        print("CHECKOUT SESSION RESPONSE")
        print(response_data)
        
        checkout_session_id = response_data.get('checkoutSessionId')
        checkout_session_url = response_data.get('checkoutSessionUrl')
        
        if checkout_session_id and checkout_session_url:
            create_checkout_session_metadata(user.user_id,
                                             checkout_session_id,
                                             req.referral_id)
        
        return response_data
    except requests.exceptions.RequestException as e:
        print("Error creating checkout session:", e)
        return {}  # Return an empty dictionary in case of error


async def webhook(request: Request) -> None:
    print("WEBHOOK REQUEST")
    body = await request.body()
    body_str = body.decode()
    print(body_str)


    # Parse JSON string into a Python dictionary
    body_dict = json.loads(body_str)

    # Extract the event type
    event_type = body_dict.get("eventType")

    if event_type == "newSubscription":
        subscription_id = body_dict.get("eventData", {}).get("newSubscription", {}).get("subscriptionId")

        checkout_session_id = body_dict.get("radomData", {}).get("checkoutSession", {}).get("checkoutSessionId")

        amount = body_dict.get("eventData", {}).get("newSubscription", {}).get("amount", {})

        radom_product_id = body_dict.get("eventData", {}).get("newSubscription", {}).get("tags", {}).get("productId")

        metadata = body_dict.get("radomData", {}).get("checkoutSession", {}).get("metadata", [])

        user_id = None
        for item in metadata:
            if item.get("key") == "user_id":
                user_id = item.get("value")

        internal_metadata = get_checkout_session_metadata(checkout_session_id)
        referral_id = internal_metadata.referral_id if internal_metadata else None

        create_payment_account(user_id=user_id, 
                               subscription_id=subscription_id, 
                               checkout_session_id=checkout_session_id, 
                               amount=amount,
                               radom_product_id=radom_product_id,
                               referral_id=referral_id)

    elif event_type == "paymentTransactionConfirmed":
        checkout_session_id = body_dict.get("radomData", {}).get("checkoutSession", {}).get("checkoutSessionId")

        payment_account = get_payment_account(user_id='',
                                              checkout_session_id=checkout_session_id)
        if payment_account and payment_account.referral_id:
            referral = referral_service.get_referral(payment_account.referral_id)

            if referral:
                referral_service.update_statistics(referral.host_id, 
                                                   payment_account.amount,
                                                   clicked=False, 
                                                   signup_ref=False)

                user = account_service.get_by_id(referral.host_id)
                if user:
                    email_service.send(user.email, 'clv2tl6jd00vybfeainihiu2j')

    elif event_type == "subscriptionExpired":
        subscription_id = body_dict.get("eventData", {}).get("newSubscription", {}).get("subscriptionId")

        remove_payment_account(subscription_id)
    elif event_type == "subscriptionCancelled":
        subscription_id = body_dict.get("eventData", {}).get("subscriptionCancelled", {}).get("subscriptionId")

        remove_payment_account(subscription_id)

    return


def cancel_plan(user: Account) -> bool:
    payment_account = get_payment_account(user.user_id)

    if payment_account:
        url = f"https://api.radom.com/subscription/{payment_account.subscription_id}/cancel"

        headers = {
            "Content-Type": "application/json",
            "Authorization": os.getenv('RADOM_ACCESS_TOKEN')
        }

        response = requests.request("POST", url, headers=headers)

        if response.status_code == 200:
            return True

    return False


def get_available_plans(user: Account) -> Optional[Dict[str, Any]]:
    # Retrieve available plans
    plans = data.get_available_plans()

    print(plans)
    
    # Get the current plan for the user
    current_plan = get_current_plan(user)

    print(current_plan)
    
    # Extract the current plan ID
    current_plan_id = current_plan.radom_product_id if current_plan else None
    
    # Return the result as a dictionary
    return {
        "plans": plans,
        "radom_product_id": current_plan_id
    }

def create_checkout_session_metadata(user_id: str, 
                                     checkout_session_id: str,
                                     referral_id: Optional[str] = None) -> None:
    
    
    return data.create_checkout_session_metadata(user_id, 
                                                 checkout_session_id,
                                                 referral_id)
    
def get_checkout_session_metadata(checkout_session_id: str) -> Optional[CheckoutSessionMetadata]:
    return data.get_checkout_session_metadata(checkout_session_id)

def get_product(radom_product_id: str) -> Optional[Plan]:
    return data.get_product(radom_product_id)


def create_payment_account(user_id: str, 
                           subscription_id: str,
                           checkout_session_id: str,
                           amount: float,
                           radom_product_id: str,
                           referral_id: Optional[str] = None):
    
    return data.create_payment_account(user_id, 
                                       subscription_id,
                                       checkout_session_id,
                                       amount,
                                       radom_product_id,
                                       referral_id)

def remove_payment_account(subscription_id: str):
    return data.remove_payment_account(subscription_id)


def get_payment_account(user_id: str, 
                        checkout_session_id: str = None) -> Optional[PaymentAccount]:
    
    return data.get_payment_account(user_id,
                                    checkout_session_id)


def get_current_plan(user: Account) -> Optional[Plan]:
    payment_account = get_payment_account(user.user_id)

    print(payment_account)

    if payment_account and payment_account.radom_product_id:
        return get_product(payment_account.radom_product_id)
