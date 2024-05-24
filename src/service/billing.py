from fastapi import Request, HTTPException

from typing import Optional, Dict, Any

import os

import requests

import json

import stripe

import base64

from stripe.error import InvalidRequestError

import data.billing as data

from model.account import Account
from model.billing import (Plan, CheckoutSessionRequest, 
                           CheckoutSessionMetadata, PaymentAccount,
                           StripeItem)

import service.account as account_service
import service.referral as referral_service

# The library needs to be configured with your account's secret key.
# Ensure the key is kept out of any version control system you might be using.
stripe.api_key = os.getenv('STRIPE_API_KEY')

# This is your Stripe CLI webhook secret for testing your endpoint locally.
endpoint_secret = os.getenv('STRIPE_ENDPOINT_SECRET')

# TODO: make a branching logic for paypal
def has_permissions(feature: str, 
                    user: Account) -> bool:
    
    # if account_service.is_insider(user):
    #     return True
    
    payment_account = get_payment_account(user.user_id)

    if payment_account and payment_account.radom_subscription_id:
        url = f"https://api.radom.com/subscription/{payment_account.radom_subscription_id}"

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
            
    elif payment_account and payment_account.stripe_subscription_id:
        try:
            subscription = stripe.Subscription.retrieve(payment_account.stripe_subscription_id)
            if subscription.status == "active":
                return True
            else:
                return False
        except stripe.error.StripeError as e:
            # Handle any Stripe API errors here
            print("Stripe API error:", e)
            return False
            
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

    print(product)

    print(req.plan_id)

    print(os.getenv('WEBAPP_DOMAIN'))

    print(user.user_id)

    print(req.referral_id)

    print(os.getenv('RADOM_ACCESS_TOKEN'))

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

    try:
        response = requests.request("POST", url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for any HTTP error
        response_data = response.json()
        print("CHECKOUT SESSION RESPONSE")
        print(response_data)
        
        radom_checkout_session_id = response_data.get('checkoutSessionId')
        checkout_session_url = response_data.get('checkoutSessionUrl')
        
        if radom_checkout_session_id and checkout_session_url:
            radom_create_checkout_session_metadata(user.user_id,
                                                   radom_checkout_session_id,
                                                   req.referral_id)
        
        return response_data
    except requests.exceptions.RequestException as e:
        print("Error creating checkout session:", e)
        return {}  # Return an empty dictionary in case of error
    

def create_stripe_checkout_session(req: CheckoutSessionRequest,
                                   user: Account) -> str:

    product = get_product(plan_id=req.plan_id)

    print(product)
    
    session = stripe.checkout.Session.create(
        success_url=f"{os.getenv('WEBAPP_DOMAIN')}/dashboard",
        cancel_url=f"{os.getenv('WEBAPP_DOMAIN')}/billing",
        line_items=[
            {
                "price": product.stripe_price_id, 
                "quantity": 1
            },
        ],
        mode="subscription",
        client_reference_id=user.user_id,
        metadata={
            "referral_id": req.referral_id
        }
    )

    return session.url


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
        radom_subscription_id = body_dict.get("eventData", {})          \
                                         .get("newSubscription", {})    \
                                         .get("subscriptionId")

        radom_checkout_session_id = body_dict.get("radomData", {})          \
                                             .get("checkoutSession", {})    \
                                             .get("checkoutSessionId")

        amount = body_dict.get("eventData", {})         \
                          .get("newSubscription", {})   \
                          .get("amount", {})

        radom_product_id = body_dict.get("eventData", {})           \
                                    .get("newSubscription", {})     \
                                    .get("tags", {})                \
                                    .get("productId")

        metadata = body_dict.get("radomData", {})           \
                            .get("checkoutSession", {})     \
                            .get("metadata", [])

        user_id = None
        for item in metadata:
            if item.get("key") == "user_id":
                user_id = item.get("value")

        internal_metadata = get_radom_checkout_session_metadata(radom_checkout_session_id)
        referral_id = internal_metadata.referral_id if internal_metadata else None

        create_payment_account(user_id=user_id, 
                               stripe_price_id=None,
                               stripe_subscription_id=None,
                               paypal_plan_id=None,
                               paypal_subscription_id=None,
                               radom_subscription_id=radom_subscription_id, 
                               radom_checkout_session_id=radom_checkout_session_id, 
                               amount=amount,
                               radom_product_id=radom_product_id,
                               referral_id=referral_id)

    elif event_type == "paymentTransactionConfirmed":
        radom_checkout_session_id = body_dict.get("radomData", {}).get("checkoutSession", {}).get("checkoutSessionId")

        payment_account = get_payment_account(user_id='',
                                              radom_checkout_session_id=radom_checkout_session_id)
        if payment_account and payment_account.referral_id:
            referral = referral_service.get_referral(payment_account.referral_id)

            referral_service.update_for_host(referral,
                                             amount)

    elif event_type == "subscriptionExpired":
        radom_subscription_id = body_dict.get("eventData", {}).get("newSubscription", {}).get("subscriptionId")

        remove_payment_account(radom_subscription_id=radom_subscription_id)
    elif event_type == "subscriptionCancelled":
        radom_subscription_id = body_dict.get("eventData", {}).get("subscriptionCancelled", {}).get("subscriptionId")

        remove_payment_account(radom_subscription_id=radom_subscription_id)

    return

async def paypal_webhook(request: Request) -> None:
    # Read the request body
    body = await request.body()
        
    # Decode the body content to a string
    body_str = body.decode("utf-8")

    # Parse the JSON string into a dictionary
    body_dict = dict(json.loads(body_str))

    # Print the parsed JSON for debugging
    print(body_dict)

    event_type = body_dict.get('event_type')
    
    if event_type is None:
        raise HTTPException(status_code=400, detail="Event type not found in request")

    # Handle subscription events
    elif event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
        print("Subscription was activated:", body)

        paypal_subscription_id = body_dict.get("resource", {}) \
                                          .get("id", {})
        
        amount = body_dict.get("resource", {})     \
                          .get("billing_info", {}) \
                          .get("last_payment", {}) \
                          .get("amount", {})       \
                          .get("value", {})
        
        paypal_plan_id = body_dict.get("resource", {}) \
                          .get("plan_id", {})
        
        user_id = body_dict.get("user_id")

        referral_id = body_dict.get("referral_id")

        create_payment_account(user_id=user_id, 
                               stripe_price_id=None,
                               stripe_subscription_id=None,
                               paypal_plan_id=paypal_plan_id,
                               paypal_subscription_id=paypal_subscription_id,
                               radom_subscription_id=None, 
                               radom_checkout_session_id=None, 
                               amount=amount,
                               radom_product_id=None,
                               referral_id=referral_id)

    # Handle subscription events
    elif event_type == "PAYMENT.SALE.COMPLETED":
        print("PAYMENT.SALE.DENIED:", body)

        sale_id = body_dict.get("resource", {}).get("id", "")

        paypal_sale = get_paypal_sale(sale_id)

        paypal_subscription_id = paypal_sale.get("billing_agreement_id", "")

        paypal_checkout_session_metadata = get_paypal_checkout_session_metadata(paypal_subscription_id)

        if paypal_checkout_session_metadata and paypal_checkout_session_metadata.referral_id:
            referral = referral_service.get_referral(paypal_checkout_session_metadata.referral_id)

            referral_service.update_for_host(referral,
                                             amount)

    # Handle subscription events
    elif event_type == "PAYMENT.SALE.DENIED":
        print("PAYMENT.SALE.DENIED:", body)

        sale_id = body_dict.get("resource", {}).get("id", "")

        paypal_sale = get_paypal_sale(sale_id)

        paypal_subscription_id = paypal_sale.get("billing_agreement_id", "")

        remove_payment_account(paypal_subscription_id)

    # Handle subscription events
    elif event_type == "PAYMENT.SALE.REFUNDED":
        print("PAYMENT.SALE.REFUNDED:", body)

        sale_id = body_dict.get("resource", {}).get("id", "")

        paypal_sale = get_paypal_sale(sale_id)

        paypal_subscription_id = paypal_sale.get("billing_agreement_id", "")

        remove_payment_account(paypal_subscription_id)

    # Handle subscription events
    elif event_type == "PAYMENT.SALE.REVERSED":
        print("PAYMENT.SALE.REVERSED:", body)

        sale_id = body_dict.get("resource", {}).get("id", "")

        paypal_sale = get_paypal_sale(sale_id)

        paypal_subscription_id = paypal_sale.get("billing_agreement_id", "")

        remove_payment_account(paypal_subscription_id)
    
    elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
        print("Subscription was cancelled", body)

        paypal_subscription_id = body_dict.get("resource", {}) \
                                          .get("id", {})
        
        remove_payment_account(paypal_subscription_id)
    
    else:
        print("Unhandled event type:", event_type)
    
    return {"status": "success"}

def get_paypal_access_token():
    credentials = f"{os.getenv('PAYPAL_CLIENT_ID')}:{'PAYPAL_CLIENT_SECRET'}"
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
    response = requests.post('https://api-m.sandbox.paypal.com/v1/oauth2/token', headers=headers, data=data)

    # Check the response
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print("Error getting access token:", response.status_code, response.json())

async def get_paypal_sale(paypal_sale_id: str) -> Optional[Dict]:
    paypal_access_token = get_paypal_access_token()

    headers = {
        'Authorization': f'Bearer {paypal_access_token}',  # Replace YOUR_ACCESS_TOKEN with your actual access token
    }

    response = requests.get(f'https://api-m.sandbox.paypal.com/v1/payments/sale/{paypal_sale_id}', headers=headers)

    if response.status_code == 200:
        sale_details = response.json()
        print("Sale details:", sale_details)
    else:
        print("Failed to retrieve sale details. Status code:", response.status_code)

async def stripe_webhook(item: StripeItem, 
                         request: Request) -> None:
    event = None
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        print(e)
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    print("EVENT: ", event)

    if event.get('type') == 'checkout.session.completed':
        session = event.get('data', {}).get('object', {})
        
        if session.get('mode') == 'subscription':
            user_id = session.get('client_reference_id')
            customer_id = session.get('customer')
            stripe_subscription_id = session.get('subscription')
            stripe_price_id = stripe.Subscription.retrieve(stripe_subscription_id) \
                                                 .get('items', {})                 \
                                                 .get('data', [{}])[0]             \
                                                 .get('price', {})                 \
                                                 .get('id')
            
            referral_id = session.get('metadata', {}).get('referral_id')

            create_stripe_account(user_id, customer_id)

            create_payment_account(user_id=user_id, 
                                   stripe_price_id=stripe_price_id,
                                   stripe_subscription_id=stripe_subscription_id,
                                   paypal_plan_id=None,
                                   paypal_subscription_id=None,
                                   radom_subscription_id=None, 
                                   radom_checkout_session_id=None, 
                                   amount=session.get("amount_total", 0) / 100,
                                   radom_product_id=None,
                                   referral_id=referral_id)
            if referral_id:
                referral = referral_service.get_referral(referral_id)
                referral_service.update_for_host(referral, session.get("amount_total", 0) / 100)

    elif event.get('type') == 'customer.subscription.deleted':
        subscription = event.get('data', {}).get('object', {})
        stripe_subscription_id = subscription.get('id')
        
        if stripe_subscription_id:
            remove_payment_account(stripe_subscription_id=stripe_subscription_id)

    elif event.get('type') == 'customer.subscription.updated':
        subscription = event.get('data', {}).get('object', {})
        stripe_subscription_id = subscription.get('id')
        
        if stripe_subscription_id:
            remove_payment_account(stripe_subscription_id=stripe_subscription_id)


    else:
        print('Unhandled event type {}'.format(event['type']))


def create_stripe_account(user_id: str, 
                          customer_id: str):
    return data.create_stripe_account(user_id, customer_id)


# TODO: create branching which based on the radom 
#       or paypal fires specific request
def cancel_plan(user: Account) -> bool:
    payment_account = get_payment_account(user.user_id)

    if payment_account and payment_account.stripe_subscription_id:
        customer_id = data.get_customer_id(user.user_id)
        
        if customer_id:
            try:
                customer = stripe.Customer.retrieve(customer_id, expand=['subscriptions'])
                if 'subscriptions' in customer:
                    subscriptions = customer.subscriptions.data  # Access the list of subscriptions
        
                    for subscription in subscriptions:  # Iterate over each subscription
                        subscription_id = subscription.id  # Access the plan ID for each subscription
                        
                        stripe.Subscription.cancel(subscription_id)
        
                        return True
            except InvalidRequestError as e:
                # Handle the case where the customer does not exist or there was an error retrieving their data
                print(f"Error cancellling subscription: {e}")
                return False
        
        return False
        
    elif payment_account and payment_account.radom_subscription_id:
        url = f"https://api.radom.com/subscription/{payment_account.radom_subscription_id}/cancel"

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
    
    # Get the current plan for the user
    current_plan = get_current_plan(user)
    
    # Return the result as a dictionary
    return {
        "plans": plans,
        "active_plan_id": current_plan.plan_id if current_plan else None
    }

def paypal_create_checkout_session_metadata(user_id: str, 
                                            paypal_subscription_id: Optional[str] = None,
                                            referral_id: Optional[str] = None) -> None:
    
    return data.paypal_create_checkout_session_metadata(user_id=user_id, 
                                                        paypal_subscription_id=paypal_subscription_id,
                                                        referral_id=referral_id)
    

def get_paypal_checkout_session_metadata(paypal_subscription_id: Optional[str] = None) -> Optional[CheckoutSessionMetadata]:
    return data.get_paypal_checkout_session_metadata(paypal_subscription_id)


def radom_create_checkout_session_metadata(user_id: str, 
                                           radom_checkout_session_id: Optional[str] = None,
                                           referral_id: Optional[str] = None) -> None:
    
    return data.radom_create_checkout_session_metadata(user_id=user_id, 
                                                       radom_checkout_session_id=radom_checkout_session_id,
                                                       referral_id=referral_id)
    

def get_radom_checkout_session_metadata(radom_checkout_session_id: Optional[str] = None) -> Optional[CheckoutSessionMetadata]:
    return data.get_radom_checkout_session_metadata(radom_checkout_session_id)


def get_product(stripe_price_id: Optional[str] = None,
                paypal_plan_id: Optional[str] = None,
                radom_product_id: Optional[str] = None,
                plan_id: Optional[str] = None) -> Optional[Plan]:
    return data.get_product(stripe_price_id, 
                            paypal_plan_id, 
                            radom_product_id,
                            plan_id)


def create_payment_account(user_id: str, 
                           stripe_price_id: str,
                           stripe_subscription_id: str,
                           paypal_plan_id: str,
                           paypal_subscription_id: str,
                           radom_subscription_id: str,
                           radom_checkout_session_id: str,
                           amount: float,
                           radom_product_id: str,
                           referral_id: Optional[str] = None):
    
    return data.create_payment_account(user_id, 
                                       stripe_price_id,
                                       stripe_subscription_id,
                                       paypal_plan_id,
                                       paypal_subscription_id,
                                       radom_subscription_id,
                                       radom_checkout_session_id,
                                       amount,
                                       radom_product_id,
                                       referral_id)


def remove_payment_account(stripe_subscription_id: Optional[str] = None,
                           paypal_subscription_id: Optional[str] = None,
                           radom_subscription_id: Optional[str] = None) -> None:
    return data.remove_payment_account(stripe_subscription_id,
                                       paypal_subscription_id,
                                       radom_subscription_id)


def get_payment_account(user_id: str, 
                        stripe_subscription_id: Optional[str] = None,
                        paypal_subscription_id: str = None,
                        radom_checkout_session_id: str = None) -> Optional[PaymentAccount]:
    
    return data.get_payment_account(user_id,
                                    stripe_subscription_id,
                                    paypal_subscription_id,
                                    radom_checkout_session_id)


def get_current_plan(user: Account) -> Optional[Plan]:
    print("GETTING CURRENT PLAN")
    payment_account = get_payment_account(user.user_id)

    print("PAYMENT ACCOUNT", payment_account)

    if payment_account:
        return get_product(stripe_price_id=payment_account.stripe_price_id,
                           paypal_plan_id=payment_account.paypal_plan_id,
                           radom_product_id=payment_account.radom_product_id)
