from fastapi import HTTPException

import os

import httpx

from typing import Optional, List, Tuple

import data.ai_verification as data

from model.account import Account
from model.ai_verification import Prompt, SocialAccount
from model.midjourney import Message, Response

import service.billing as billing_service
import service.usage_history as usage_history_service
import service.midjourney as midjourney_service

# TODO: you can make one request every 3 seconds - so we have to have some queue for the users

# async def faceswap(source_uri: str,
#                    target_uri: str, 
#                    user: Account) -> None:
#     if billing_service.has_permissions('ai_verification', user):
#         url = "https://api.mymidjourney.ai/api/v1/midjourney/faceswap"
#         headers = {
#             "Content-Type": "application/json",
#             "Authorization": f"Bearer {os.getenv('MIDJOURNEY_TOKEN')}",
#         }
#         data = {
#             "source": source_uri,
#             "target": target_uri,
#             "ref": user.user_id,
#             "webhookOverride": f"{os.getenv('ROOT_DOMAIN')}/midjourney/webhook"
#         }

        
#         async with httpx.AsyncClient() as client:
#             print("MAKING REQUEST TO MIDJOURNEY FACESWAP ENDPOINT API")
#             resp = await client.post(url, headers=headers, json=data)
#             response_data = Response.parse_raw(resp.text)

#         if response_data.success:
#             usage_history_service.update('ai_verification', user.user_id)

#         if resp.status_code != 200 or response_data.error:
#             raise HTTPException(status_code=500, detail="Faceswap failed")
        
#         print(response_data)
#     else:
#         raise HTTPException(status_code=403, detail="Upgrade your plan to unlock permissions.")


# async def commands(command: str,
#                    user: Account) -> None:
#         url = "https://api.mymidjourney.ai/api/v1/midjourney/commands"
#         headers = {
#             "Content-Type": "application/json",
#             "Authorization": f"Bearer {os.getenv('MIDJOURNEY_TOKEN')}",
#         }
#         data = {
#             "cmd": command,
#             "ref": user.user_id,
#             "webhookOverride": f"{os.getenv('ROOT_DOMAIN')}/midjourney/webhook"
#         }


#         async with httpx.AsyncClient() as client:
#             print("MAKING REQUEST TO MIDJOURNEY COMMANDS ENDPOINT API")
#             resp = await client.post(url, headers=headers, json=data)
#             print("PARSING RESPONSE")
#             if resp.status_code == 401:
#                 print("Unauthorized: Authentication failure.")
#                 return None
#             print(resp.text)
#             response_data = resp.json()

#         if resp.status_code != 200 or "error" in response_data:
#             raise HTTPException(status_code=400, detail="Command failed")
        
#         return response_data

def check_prompt(prompt: Prompt):
    versions = ['1', '2', '3', '4', '5', '5.0', '5.1', '5.2', '6']
    if prompt.version != '' and (prompt.version not in versions):
        return f"Error: version must be one of {versions}"
    
    if prompt.style != '':
        if prompt.style != "raw":
            return "Error: style must be either none or raw"
        if prompt.version == '' or (prompt.version != '' and prompt.version not in versions[-3:]):
            return f"Error: incorrect version. Supported versions for raw style: {versions[-3:]}"
        
    # TODO: what about aspect ratios? which are valid?

    if prompt.stop != '' and (int(prompt.stop) < 10 or 100 < int(prompt.stop)):
        return "Error: stop must be between 10 and 100"
    
    if prompt.stylize != '':
        if prompt.stylize != '' and (int(prompt.stylize) < 0 or 1000 < int(prompt.stylize)):
            return "Error: stylize must be between 0 and 1000"
        if prompt.version == '' or (prompt.version != '' and prompt.version not in versions[-2:]):
            return f"Error: incorrect version. Supported versions for stylize: {versions[-2:]}"
        
    if prompt.seed != '' and (int(prompt.seed) < 0 or 4294967295 < int(prompt.seed)):
        return "Error: seed must be between 0 and 4294967295"

    return True


def create_prompt_string(prompt: Prompt,
                         img_ref_cdn_url_list: Optional[List[str]] = None,
                         cref_cdn_url_list: Optional[List[str]] = None,
                         sref_cdn_url_list: Optional[List[str]] = None) -> str:
    attributes = ["version", "style", "stop", "stylize", "seed"]

    # Start with an empty prompt string
    prompt_string = ""

    # Add image references at the start of the prompt string
    if img_ref_cdn_url_list:
        prompt_string = " ".join(img_ref_cdn_url_list) + " "

    # Add the main prompt
    prompt_string += prompt.prompt if prompt.prompt else ""

    # Add additional attributes
    attributes_string = " ".join(
        [f" --{attr} {getattr(prompt, attr)}" for attr in attributes if getattr(prompt, attr) is not None and getattr(prompt, attr) != ""]
    )
    
    # Concatenate the attributes string to the prompt string
    prompt_string += f" {attributes_string}"

    # Add width and height as aspect ratio if both are provided
    if prompt.width and int(prompt.width) > 0 and prompt.height and int(prompt.height) > 0:
        prompt_string += f" --aspect {prompt.width}:{prompt.height}"
    
    if cref_cdn_url_list:
        cref_string = " ".join(cref_cdn_url_list)
        prompt_string += f" --cref {cref_string}"

    if sref_cdn_url_list:
        sref_string = " ".join(sref_cdn_url_list)
        prompt_string += f" --sref {sref_string}"

    print("CONSTRUCTED A PROMPT: ", prompt_string)

    return prompt_string


async def increase_speed() -> bool:
    try:
        # Make a request to activate fast mode
        fast_url = "https://api.mymidjourney.ai/api/v1/midjourney/commands"
        fast_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('MIDJOURNEY_TOKEN')}",
        }
        fast_data = {
            "cmd": "fast"
        }

        async with httpx.AsyncClient() as client:
            fast_resp = await client.post(fast_url, headers=fast_headers, json=fast_data)
            print(f"Fast mode response status: {fast_resp.status_code}")
            print(f"Fast mode response body: {fast_resp.text}")

            if fast_resp.status_code != 200:
                print("Failed to activate fast mode.")
                return False

            response_json = fast_resp.json()
            error_message = response_json.get("message", "")

            if response_json.get("success", False):
                if error_message:
                    print(f"Fast mode activated but with error: {error_message}")
                    if "turbo hours" in error_message.lower():
                        print("Turbo hours have run out.")
                        return False
                return True
            else:
                print(f"Fast mode activation failed: {error_message}")
                return False

    except Exception as e:
        print(f"Error increasing speed: {e}")
        return False


async def imagine(prompt: Prompt, 
                  user: Account,
                  img_ref_cdn_url_list: Optional[List[str]] = None,
                  cref_cdn_url_list: Optional[List[str]] = None,
                  sref_cdn_url_list: Optional[List[str]] = None) -> None:
        # docs: (https://docs.midjourney.com/docs/)
        #
        # prompt: image_urls (optional) text_prompt parameters (--parameter1 --parameter2)
        # parameters:
        # - version: --version x    ; accepts the values 1, 2, 3, 4, 5, 5.0, 5.1, 5.2, and 6.
        # - style: --style raw  ; Model Versions 6, 5.2, 5.1 and Niji 6 accept this parameter
        # - aspect ratio: --aspect x:y  ; where x and y are numbers for all the ratios
        # - stop: --stop x   ; accepts the values 10–100.
        # - stylize: --stylize x   ; default value is 100 and accepts integer values 0–1000
        # - seed: --seed x  ; accepts whole numbers 0–4294967295

        # - generation speed: --fast or --relax  ; paramters are only available for the pro or mega plan - call the 
        #   commands for each user in imagine endpoint before running the prompt however this is tricky becuase the backend 
        #   endpoints are async so we have to in v2 guarantee that users are in the request queue and commands post request 
        #   and imagine post request run in batch  only fast and relax are accepted 
        #   see docs: https://www.mymidjourney.ai/docs/commands                                                                                                 
        # - quality: --quality x    ; only accepts the values: .25, .5, and 1 for the current model. Larger values are rounded down to 1

    print("CHECKING PERMISSIONS")
    if billing_service.has_permissions("AI Dating App Verification", user):
        print("CHECKING PROMPT PASSED: ", prompt)
        check = check_prompt(prompt)
        if check is not True:
            print(check)
            raise HTTPException(status_code=400, detail=check)
        
        print("CREATING PAYLOAD")
        url = "https://api.mymidjourney.ai/api/v1/midjourney/imagine"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('MIDJOURNEY_TOKEN')}",
        }

        prompt_string = create_prompt_string(prompt,
                                             img_ref_cdn_url_list,
                                             cref_cdn_url_list,
                                             sref_cdn_url_list)

        # turbo = await increase_speed()

        # if turbo:
        #     prompt_string += " --turbo"

        data = {
            "prompt": prompt_string,
            "ref": user.user_id,
            "webhookOverride": f"{os.getenv('ROOT_DOMAIN')}/midjourney/webhook"
        }

        async with httpx.AsyncClient() as client:
            print("MAKING REQUEST TO MIDJOURNEY IMAGINE ENDPOINT API")
            resp = await client.post(url, headers=headers, json=data)
            response_data = Response.parse_raw(resp.text)

            if response_data.success:
                usage_history_service.update("ai_verification", user.user_id)

            if resp.status_code != 200 or response_data.error:
                raise HTTPException(status_code=500, detail="Prompt execution failed.")
            
            print(response_data)
            
            # # Serialize response data using jsonable_encoder
            return response_data
    else:
        raise HTTPException(status_code=403, detail="Upgrade your plan to unlock permissions.")


async def action(messageId: str, 
                 button: str, 
                 user: Account) -> None:

    if not billing_service.has_permissions("AI Dating App Verification", user):
        raise HTTPException(status_code=403, detail="Upgrade your plan to unlock permissions.")

    if not midjourney_service.valid_button(messageId, button):
        raise HTTPException(status_code=405, detail="Requested action is not valid.")
    
    url = "https://api.mymidjourney.ai/api/v1/midjourney/button"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('MIDJOURNEY_TOKEN')}",
    }
    data = {
        "messageId": messageId,
        "button": button,
        "ref": user.user_id,
        "webhookOverride": f"{os.getenv('ROOT_DOMAIN')}/midjourney/webhook"
    }

    # turbo = await increase_speed(user)

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=data)
        response_data = Response.parse_raw(resp.text)

    if response_data.success:
        usage_history_service.update('ai_verification', user.user_id)

    if resp.status_code != 200 or response_data.error:
        raise HTTPException(status_code=400, detail="Action failed")

    print("AI VERIF DATA SENT")
    print(response_data)

    return response_data


def add_account(social_account: SocialAccount,
                prompt: Prompt,
                user: Account) -> Optional[Tuple[SocialAccount, Prompt]]:
    try:
        return data.add_account(social_account, 
                                prompt,
                                user.user_id)
    except ValueError:
        raise HTTPException(status_code=500, detail="Failed to add account")


def update_account(social_account: SocialAccount) -> None:
    try:
        data.update_account(social_account)
    except ValueError:
        raise HTTPException(status_code=500, detail="Failed to update social account")
    

def delete_account(account_id: str) -> None:
    try:
        data.delete_account(account_id)
    except ValueError:
        raise HTTPException(status_code=500, detail="Failed to delete social account")


def get_accounts(user: Account) -> Optional[List[SocialAccount]]:
    return data.get_accounts(user.user_id)


def update_prompt(prompt: Prompt) -> None:
    try:
        data.update_prompt(prompt)
    except ValueError:
        raise HTTPException(status_code=500, detail="Failed to update prompt")


def get_prompts(user: Account) -> Optional[List[Prompt]]:
    return data.get_prompts(user.user_id)


def get_message(messageId: str) -> Optional[Message]:
    return midjourney_service.get_message(messageId)


def get_history(user: Account) -> List[Message]:
    return midjourney_service.get_history(user)

# async def cancel_job(messageId: str,
#                      user: Account) -> None:
#     url = "https://api.mymidjourney.ai/api/v1/midjourney/button"
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {os.getenv('MIDJOURNEY_TOKEN')}",
#     }
#     data = {
#         "messageId": messageId,
#         "button": "Cancel Job",
#         "ref": user.user_id,
#         "webhookOverride": f"{os.getenv('ROOT_DOMAIN')}/midjourney/webhook"
#     }

#     async with httpx.AsyncClient() as client:
#         resp = await client.post(url, headers=headers, json=data)
#         response_data = Response.parse_raw(resp.text)

#     if resp.status_code != 200 or response_data.error:
#         raise HTTPException(status_code=500, detail="Failed to cancel a job.")
    
#     print(response_data)