from fastapi import Request, HTTPException

from typing import Optional, Dict, Any

import os

import requests

import json

import pprint

import gocardless_pro

from uuid import uuid4

import base64

import data.billing as data

from model.account import Account

from model.billing import (Plan, RadomCheckoutRequest, 
                           RadomCheckoutSessionMetadata, PaymentAccount,
                           PaypalCheckoutMetadata, GCRequest)

import service.account as account_service

import service.email as email_service

import service.referral as referral_service

from datetime import datetime

def has_permissions(feature: str, 
                    user: Account) -> bool:
    
    if account_service.is_insider(user):
        return True

    plan = get_current_plan(user)

    if plan and feature in plan.features:
        return True
            
    return False

# TODO: test the expired subscription for radom and paypal

def create_radom_checkout_session(
    req: RadomCheckoutRequest,
    user: Account
) -> Dict[str, Any]:
    payment_account = get_payment_account(user_id=user.user_id)

    if payment_account and payment_account.status == "active":
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
        "successUrl": f"{os.getenv('WEBAPP_DOMAIN')}/transaction-processed",
        "cancelUrl": f"{os.getenv('WEBAPP_DOMAIN')}/transaction-failed",
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

    print("CREATING RADOM CHECKOUT SESSION...")
    try:
        response = requests.request("POST", url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for any HTTP error
        response_data = response.json()
        print(f"RADOM RESPONSE: {response_data}")
        
        radom_checkout_session_id = response_data.get('checkoutSessionId')
        
        print("CHECKING IF RADOM CHECKOUT SESSION ID IS NULL...")
        if radom_checkout_session_id:
            print("RADOM CHECKOUT SESSION ID IS NOT NULL")
            radom_create_checkout_session_metadata(user.user_id,
                                                   radom_checkout_session_id,
                                                   req.referral_id)
        else:
            print("RADOM CHECKOUT SESSION ID IS NULL")
        
        return response_data
    except requests.exceptions.RequestException as e:
        print("Error creating checkout session:", e)
        return {}  # Return an empty dictionary in case of error


async def radom_webhook(request: Request) -> None:
    body = await request.body()
    body_str = body.decode()

    # Parse JSON string into a Python dictionary
    body_dict = json.loads(body_str)

    print(f"RADOM REQUEST BODY: {body_dict}")

    # Extract the event type
    event_type = body_dict.get("eventType")

    if event_type == "newSubscription":
        print("EVENT: NEW SUBSCRIPTION")

        print("GETTING RADOM SUBSCRIPTION ID...")
        radom_subscription_id = body_dict.get("eventData", {})          \
                                         .get("newSubscription", {})    \
                                         .get("subscriptionId")
        
        print(f"GOT RADOM SUBSCRIPTION ID: {radom_subscription_id}")

        print("GETTING RADOM CHECKOUT SESSION ID...")
        radom_checkout_session_id = body_dict.get("radomData", {})          \
                                             .get("checkoutSession", {})    \
                                             .get("checkoutSessionId")
        
        print(f"GOT RADOM CHECKOUT SESSION ID: {radom_checkout_session_id}")

        print("GETTING AMOUNT...")
        amount = body_dict.get("eventData", {})         \
                          .get("newSubscription", {})   \
                          .get("amount", {})
        
        print(f"GOT AMOUNT: {amount}")


        print("GETTING RADOM PRODUCT ID...")
        radom_product_id = body_dict.get("eventData", {})           \
                                    .get("newSubscription", {})     \
                                    .get("tags", {})                \
                                    .get("productId")
        
        print(f"GOT PRODUCT ID: {radom_product_id}")

        print("GETTING METADATA...")
        metadata = body_dict.get("radomData", {})           \
                            .get("checkoutSession", {})     \
                            .get("metadata", [])
        
        print(f"GOT METADATA: {metadata}")

        print("TRYING TO FIND USER ID IN METADATA...")
        user_id = None
        for item in metadata:
            if item.get("key") == "user_id":
                user_id = item.get("value")
                print(f"Found user_id in metadata: {user_id}")
                break

        if not user_id:
            print(f"USER ID IS NONE: {user_id}")

        internal_metadata = get_radom_checkout_session_metadata(radom_checkout_session_id)

        print(f"GOT RADOM CHECKOUT SESSION METADATA: {internal_metadata}")

        referral_id = internal_metadata.referral_id if internal_metadata else None

        print(f"GOT REFERRAL ID FROM CHECKOUT SESSION METADATA: {referral_id}")

        create_payment_account(user_id=user_id, 
                               provider="radom",
                               paypal_plan_id=None,
                               paypal_subscription_id=None,
                               radom_subscription_id=radom_subscription_id, 
                               radom_checkout_session_id=radom_checkout_session_id, 
                               amount=amount,
                               radom_product_id=radom_product_id,
                               gc_billing_request_id=None,
                               gc_subscription_id=None,
                               plan_id=None,
                               referral_id=referral_id,
                               status="active")
        
        account = account_service.get_by_id(user_id=internal_metadata.user_id)

        email_service.send(account.email, 
                           "clwxmnsll00vvrmqenbal0jln",
                           username=account.username,
                           discord_link=os.getenv("DISCORD_LINK"))
        
        if payment_account and referral_id:
            referral = referral_service.get_referral(referral_id)

            print(f"FOUND REFERRAL MODAL: {referral}")

            referral_service.update_for_host(referral,
                                             payment_account.amount,
                                             subscription_cancelled=False)
        
    elif event_type == "subscriptionExpired":
        radom_subscription_id = body_dict.get("eventData", {}).get("newSubscription", {}).get("subscriptionId")

        set_payment_account_status(radom_subscription_id=radom_subscription_id,
                                   status="disabled")
        
        account = account_service.get_by_id(user_id=internal_metadata.user_id)

        email_service.send(account.email, 
                           "clwy121tq01hh7cvn4qwz3rjc",
                           username=account.username,
                           discord_link=os.getenv("DISCORD_LINK"))
        
    elif event_type == "subscriptionCancelled":
        radom_subscription_id = body_dict.get("eventData", {}).get("subscriptionCancelled", {}).get("subscriptionId")

        payment_account = get_payment_account(radom_subscription_id=radom_subscription_id)

        internal_metadata = get_radom_checkout_session_metadata(payment_account.radom_checkout_session_id)

        set_payment_account_status(user_id=internal_metadata.user_id,
                                   status="cancelled")
        
        account = account_service.get_by_id(user_id=internal_metadata.user_id)

        email_service.send(account.email, 
                           "clwxm0der014zw2uff7l0pu9w",
                           username=account.username,
                           discord_link=os.getenv("DISCORD_LINK"))

    return


async def paypal_webhook(request: Request) -> None:
    # Read the request body
    body = await request.body()
        
    # Decode the body content to a string
    body_str = body.decode("utf-8")

    # Parse the JSON string into a dictionary
    body_dict = dict(json.loads(body_str))

    print(f"PAYPAL REQUEST BODY: {body_dict}")

    event_type = body_dict.get('event_type')

    print("EVENT TYPE: ", event_type)
    
    if event_type is None:
        raise HTTPException(status_code=400, detail="Event type not found in request")

    # TODO: only on successful dispute we makr the payment account as disabled

    elif event_type == "BILLING.SUBSCRIPTION.ACTIVATED":
        print("EVENT: BILLING.SUBSCRIPTION.ACTIVATED")

        print("GETTING PAYPAL SUBSCRIPTION ID...")
        paypal_subscription_id = body_dict.get("resource", {}) \
                                          .get("id", {})
        print(f"GOT PAYPAL SUBSCRIPTION ID: {paypal_subscription_id}")
        
        print("GETTING AMOUNT...")
        amount = body_dict.get("resource", {})     \
                          .get("billing_info", {}) \
                          .get("last_payment", {}) \
                          .get("amount", {})       \
                          .get("value", {})
        print(f"GOT AMOUNT: {amount}")
        
        print("GETTING PAYPAL PLAN ID...")
        paypal_plan_id = body_dict.get("resource", {}) \
                                  .get("plan_id", {})
        print(f"GOT PAYPAL PLAN ID: {paypal_plan_id}")
        
        print("GETTING CUSTOM ID...")
        custom_id = body_dict.get("resource", {}) \
                              .get("custom_id", {})
        print(f"GOT CUSTOM ID: {custom_id}")
        
        internal_metadata = get_paypal_checkout_metadata(custom_id)

        payment_account = create_payment_account(user_id=internal_metadata.user_id,
                                                 provider="paypal",
                                                 paypal_plan_id=paypal_plan_id,
                                                 paypal_subscription_id=paypal_subscription_id,
                                                 radom_subscription_id=None, 
                                                 radom_checkout_session_id=None, 
                                                 amount=amount,
                                                 radom_product_id=None,
                                                 gc_billing_request_id=None,
                                                 gc_subscription_id=None,
                                                 plan_id=None,
                                                 referral_id=internal_metadata.referral_id,
                                                 status="active")
        
        account = account_service.get_by_id(user_id=internal_metadata.user_id)

        email_service.send(account.email, 
                           "clwxmnsll00vvrmqenbal0jln",
                           username=account.username,
                           discord_link=os.getenv("DISCORD_LINK"))


    elif event_type == "BILLING.SUBSCRIPTION.EXPIRED":
        print("EVENT: BILLING.SUBSCRIPTION.EXPIRED")
        
        print("GETTING CUSTOM ID...")
        subscription_id = body_dict.get("id", {})

        print(f"GOT SUBSCRIPTION ID: {subscription_id}")
    
        set_payment_account_status(paypal_subscription_id=subscription_id,
                                   status="disabled")
        
        account = account_service.get_by_id(user_id=internal_metadata.user_id)

        email_service.send(account.email, 
                           "clwy121tq01hh7cvn4qwz3rjc",
                           username=account.username,
                           discord_link=os.getenv("DISCORD_LINK"))
    
    elif event_type == "PAYMENT.SALE.COMPLETED":
        print(f"EVENT: PAYMENT SALE COMPLETED")

        print("GETTING CUSTOM ID...")
        custom_id = body_dict.get("resource", {}) \
                              .get("custom", {})
        print(f"GOT CUSTOM ID: {custom_id}")
        
        internal_metadata = get_paypal_checkout_metadata(custom_id)

        account = account_service.get_by_id(user_id=internal_metadata.user_id)

        email_service.send(account.email, 
                           "clwxmcrp7005y5htkedf5th36",
                           username=account.username,
                           discord_link=os.getenv("DISCORD_LINK"))

        payment_account = get_payment_account(user_id=internal_metadata.user_id)

        print("CHECKING IF ACCOUNT IS FROM REFERRAL")
        if payment_account and internal_metadata.referral_id:
            referral = referral_service.get_referral(internal_metadata.referral_id)

            print(f"FOUND REFERRAL MODAL: {referral}")

            referral_service.update_for_host(referral,
                                             payment_account.amount,
                                             subscription_cancelled=False)
        else:
            print("ACCOUNT IS NOT FROM REFERRAL")

    # TODO: we mark the payment account as disabled and 
    elif event_type == "BILLING.SUBSCRIPTION.PAYMENT.FAILED":
        print(f"EVENT: BILLING SUBSCRIPTION PAYMENT FAILED")

        print("GETTING CUSTOM ID...")
        custom_id = body_dict.get("resource", {}) \
                              .get("custom", {})
        print(f"GOT CUSTOM ID: {custom_id}")
        
        internal_metadata = get_paypal_checkout_metadata(custom_id)

        set_payment_account_status(user_id=internal_metadata.user_id,
                                   status="disabled")

        account = account_service.get_by_id(user_id=internal_metadata.user_id)

        email_service.send(account.email, 
                           "clwxmnsll00vvrmqenbal0jln",
                           username=account.username,
                           discord_link=os.getenv("DISCORD_LINK"))

    # Handle subscription events
    elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
        print(f"EVENT: BILLING SUBSCRIPTION CANCELLED")

        print("GETTING CUSTOM ID...")
        custom_id = body_dict.get("resource", {}) \
                              .get("custom_id", {})
        print(f"GOT CUSTOM ID: {custom_id}")
        
        internal_metadata = get_paypal_checkout_metadata(custom_id)

        set_payment_account_status(user_id=internal_metadata.user_id,
                                   status="cancelled")

        account = account_service.get_by_id(user_id=internal_metadata.user_id)

        email_service.send(account.email, 
                           "clwxm0der014zw2uff7l0pu9w",
                           username=account.username,
                           discord_link=os.getenv("DISCORD_LINK"))
    else:
        print("Unhandled event type:", event_type)
    
    return {"status": "success"}


async def create_gc_checkout_session(req: GCRequest,
                                     user: Account) -> str:
    client = gocardless_pro.Client(access_token=os.getenv("GC_ACCESS_TOKEN"), environment=os.getenv("GC_MODE"))

    plan = get_product(plan_id=req.plan_id)

    billing_request = client.billing_requests.create(params={
        "payment_request": {
            "description": plan.name,
            "amount": f"{int(plan.price*100)}",
            "currency": "GBP",
            "app_fee": f"{int(plan.price*100)}"
        },
        "mandate_request": {
            "scheme": "bacs"
        }
    })

    print("\nBILLING REQUEST:")
    pprint.pprint(vars(billing_request))

    # Extract the billing request ID
    billing_request_id = billing_request.id
    print("\nBILLING REQUEST ID:", billing_request_id)

    billing_request_flow = client.billing_request_flows.create(params={
        "redirect_uri": "https://cloud.cupidai.tech/transaction-processed",
        "exit_uri": "https://cloud.cupidai.tech/transaction-failed",
        "links": {
            "billing_request": billing_request_id
        }
    })

    create_payment_account(user_id=user.user_id,
                           provider="gc",
                           paypal_plan_id=None,
                           paypal_subscription_id=None,
                           radom_subscription_id=None, 
                           radom_checkout_session_id=None, 
                           amount=plan.price,
                           radom_product_id=None,
                           gc_billing_request_id=billing_request_id,
                           gc_subscription_id=None,
                           gc_mandate_count=0,
                           plan_id=plan.plan_id,
                           referral_id=req.referral_id,
                           status="disabled")

    print("\nBILLING REQUEST FLOW:")
    pprint.pprint(vars(billing_request_flow))


    # Extract and print the authorization URL
    authorisation_url = billing_request_flow.attributes['authorisation_url']
    print("\nAUTHORISATION URL:", authorisation_url)

    return authorisation_url

async def gc_webhook(request: Request):
    payload = await request.json()
    print("GC REQUEST BODY:", json.dumps(payload, indent=4))

    for event in payload.get("events", []):
        action = event.get("action")
        resource_type = event.get("resource_type")

        if resource_type == "payments" and action == "confirmed":
            print("#################################################################")
            print("PAYMENT ACTIVE")
            billing_request = event.get("links").get("billing_request")

            set_payment_account_status(gc_billing_request_id=billing_request,
                                       status="active")
            
            print("MARKED PAYMENT AS ACTIVE")
            
        elif resource_type == "mandates" and action == "created":
            billing_request = event.get("links").get("billing_request")
            mandate = event.get("links").get("mandate")

            payment_account = get_payment_account(gc_billing_request_id=billing_request)

            if payment_account.gc_mandate_count == 1:
                print("#################################################################")
                print("PAYMENT HAS BEEN COMPLETED")

                client = gocardless_pro.Client(
                    access_token=os.getenv("GC_ACCESS_TOKEN"),
                    environment=os.getenv("GC_MODE")
                )

                plan = get_product(plan_id=payment_account.plan_id)

                print("CREATING SUBSCRIPTION")

                subscription = client.subscriptions.create(
                    params={
                        "amount" : int(plan.price*100),
                        "currency" : "GBP",
                        "interval_unit" : "monthly",
                        "day_of_month" : str(datetime.now().day),
                        "links": {
                            "mandate": mandate
                        },
                        "metadata": {
                            "subscription_number": str(uuid4())
                        }
                    }, headers={
                        'Idempotency-Key': str(uuid4())
                })

                print("SUBSCRIPTION CREATED:", subscription)

                payment_account = create_payment_account(gc_billing_request_id=billing_request,
                                                         gc_subscription_id=subscription.id,
                                                         status="active")
                
                account = account_service.get_by_id(user_id=payment_account.user_id)

                email_service.send(account.email, 
                                   "clwxmnsll00vvrmqenbal0jln",
                                   username=account.username,
                                   discord_link=os.getenv("DISCORD_LINK"))
                
                # if payment_account and payment_account.referral_id:
                #     referral = referral_service.get_referral(payment_account.referral_id)

                #     print(f"FOUND REFERRAL MODAL: {referral}")

                #     referral_service.update_for_host(referral,
                #                                      payment_account.amount,
                #                                      subscription_cancelled=False)
                
            create_payment_account(gc_billing_request_id=billing_request,
                                   gc_mandate_count=1)

        elif resource_type == "subscriptions" and action == "cancelled":
            subscription_id = event.get("links").get("subscription")
            
            payment_account = create_payment_account(gc_billing_request_id=None,
                                                     gc_subscription_id=subscription_id,
                                                     gc_mandate_count=-2,
                                                     status="cancelled")
            
            account = account_service.get_by_id(user_id=payment_account.user_id)

            email_service.send(account.email, 
                               "clwxm0der014zw2uff7l0pu9w",
                               username=account.username,
                               discord_link=os.getenv("DISCORD_LINK"))
            
    return {"status": "ok"}


def paypal_create_checkout_metadata(referral_id: Optional[str], 
                                    user: Account) -> Optional[str]:
    uuid = str(uuid4())
    return data.paypal_create_checkout_metadata(referral_id,
                                                uuid,
                                                user.user_id)


def get_paypal_checkout_metadata(uuid: str) -> Optional[PaypalCheckoutMetadata]:
    return data.get_paypal_checkout_metadata(uuid)


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

    payment_account = get_payment_account(user_id=user.user_id)
    
    if payment_account and hasattr(payment_account, 'paypal_subscription_id') \
       and payment_account.paypal_subscription_id is not None \
       and payment_account.provider == "paypal":
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
         and payment_account.provider == "radom":
        url = f"https://api.radom.com/subscription/{payment_account.radom_subscription_id}/cancel"

        headers = {
            "Content-Type": "application/json",
            "Authorization": os.getenv('RADOM_ACCESS_TOKEN')
        }

        response = requests.request("POST", url, headers=headers)

        if response.status_code == 200:
            return True
        
    elif payment_account and hasattr(payment_account, 'gc_billing_request_id') \
         and payment_account.gc_billing_request_id is not None \
         and payment_account.provider == "gc":
        
        client = gocardless_pro.Client(access_token=os.getenv("GC_ACCESS_TOKEN"), environment=os.getenv("GC_MODE"))

        if payment_account.gc_subscription_id:
            res = client.subscriptions.cancel(payment_account.gc_subscription_id)
            print("CANCELLED GC SUBSCRIPTION:", res)
        else:
            print("PAYMENT ACCOUNT IS NOT VIABLE FOR PLAN CANCELLATION:", payment_account)

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


def radom_create_checkout_session_metadata(user_id: str, 
                                           radom_checkout_session_id: Optional[str] = None,
                                           referral_id: Optional[str] = None) -> None:
    return data.radom_create_checkout_session_metadata(user_id=user_id, 
                                                       radom_checkout_session_id=radom_checkout_session_id,
                                                       referral_id=referral_id)
    

def get_radom_checkout_session_metadata(radom_checkout_session_id: Optional[str] = None) -> Optional[RadomCheckoutSessionMetadata]:
    return data.get_radom_checkout_session_metadata(radom_checkout_session_id)


def get_product(paypal_plan_id: Optional[str] = None,
                radom_product_id: Optional[str] = None,
                plan_id: Optional[str] = None) -> Optional[Plan]:
    return data.get_product(paypal_plan_id, 
                            radom_product_id,
                            plan_id)


def create_payment_account(user_id: Optional[str] = None,
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
    
    return data.create_payment_account(user_id, 
                                       provider,
                                       paypal_plan_id,
                                       paypal_subscription_id,
                                       radom_subscription_id,
                                       radom_checkout_session_id,
                                       amount,
                                       radom_product_id,
                                       gc_billing_request_id,
                                       gc_subscription_id,
                                       gc_mandate_count,
                                       plan_id,
                                       status,
                                       referral_id)


def set_payment_account_status(user_id: Optional[str] = None,
                               paypal_subscription_id: Optional[str] = None,
                               radom_subscription_id: Optional[str] = None,
                               gc_billing_request_id: Optional[str] = None,
                               gc_subscription_id: Optional[str] = None,
                               status: Optional[str] = None) -> None:
    return data.set_payment_account_status(user_id,
                                           paypal_subscription_id,
                                           radom_subscription_id,
                                           gc_billing_request_id,
                                           gc_subscription_id,
                                           status)


def get_payment_account(user_id: str = None,
                        paypal_subscription_id: str = None,
                        radom_checkout_session_id: str = None,
                        radom_subscription_id: str = None,
                        gc_billing_request_id: str = None) -> Optional[PaymentAccount]:
    
    return data.get_payment_account(user_id,
                                    paypal_subscription_id,
                                    radom_checkout_session_id,
                                    radom_subscription_id,
                                    gc_billing_request_id)


def get_current_plan(user: Account) -> Optional[Plan]:
    payment_account = get_payment_account(user.user_id)

    if payment_account and (payment_account.status == "active"):
        return get_product(paypal_plan_id=payment_account.paypal_plan_id,
                           radom_product_id=payment_account.radom_product_id,
                           plan_id=payment_account.plan_id)