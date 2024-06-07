from fastapi import BackgroundTasks, HTTPException

from typing import Dict, List, Optional

from uuid import uuid4

import os

import re

import json

from pyuploadcare import Uploadcare

import requests

from comfyui.ModelInterface import generate_workflow

import data.image_generation as data

from model.account import Account
from model.image_generation import Settings, Message

import service.billing as billing_service
import service.usage_history as usage_history_service


def webhook(message: Message) -> None:
    print(message)
    update_message(user_id=message.user_id, 
                   message_id=message.message_id, 
                   status=message.status, 
                   s3_uris=message.s3_uris)

    if message.status == 'in progress':
        usage_history_service.update('image_generation', message.user_id)


def save_settings(settings: Settings):
    return data.save_settings(settings)


def update_message(user_id: str, 
                   status: Optional[str] = None, 
                   message_id: Optional[str] = None, 
                   s3_uris: Optional[List[str]] = None):
    
    return data.update_message(user_id, 
                               status, 
                               message_id, 
                               s3_uris)


def extract_id_from_uri(uri):
    # Use regex to extract the UUID from the URI
    match = re.search(r"/([a-f0-9-]+)/", uri)
    if match:
        return match.group(1)
    else:
        return None
    

def map_model(curr_model):
    model = "epicphotogasm_lastUnicorn.safetensors"

    if curr_model == 'Realistic':
        model = "epicphotogasm_lastUnicorn.safetensors"
    elif curr_model == 'Cartoony Anime':
        model = "chilloutmix_NiPrunedFp32Fix.safetensors"
    elif curr_model == 'Amateur':
        model = "stablegramUSEuropean_v21.safetensors"
    elif curr_model == 'Semi Realistic':
        model =  "edgeOfRealism_eorV20Fp16BakedVAE.safetensors"

    return model

    
def send_post_request(url: str, headers: dict, payload: dict) -> None:
    requests.post(url, headers=headers, json=payload)


def get_image_path(image_url: str):
    if image_url:
        uploadcare = Uploadcare(public_key=os.getenv('UPLOADCARE_PUBLIC_KEY'), secret_key=os.getenv('UPLOADCARE_SECRET_KEY'))

        image_id = extract_id_from_uri(image_url)
        image_format = uploadcare.file(image_id).info['mime_type'].split('/')[1]

        if image_format not in ['jpeg', 'png']:
            raise HTTPException(status_code=400, detail=f"Invalid {image_format} image format. Valid ones are jpeg and png.")
        
        predefined_path = os.getenv('COMFYUI_PREDEFINED_PATH')
        path = predefined_path + "/" + image_id + f".{image_format}"
    
        return path


async def generate(settings: Settings, 
                   user: Account, 
                   background_tasks: BackgroundTasks) -> None:
    if billing_service.has_permissions("Realistic AI Content Creation", user):
        
        
        reference_image_path = get_image_path(settings.reference_image_url)
        controlnet_reference_image_path = get_image_path(settings.controlnet_reference_image_url)

        message_id = update_message(user_id=user.user_id, 
                                    status="started", 
                                    message_id=None, 
                                    s3_uris=None)
        
        if settings.model:
            settings.model = map_model(settings.model)

        print("SETTINGS:", settings)

        workflow = generate_workflow(settings,
                                     reference_image_path,
                                     controlnet_reference_image_path)
        
        # Specify the file path
        file_path = '/data.json'

        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Open the file in write mode and use json.dump to write the data
        with open(file_path, 'w') as file:
            json.dump(workflow, file, indent=2)  # indent=4 for pretty printing

        if workflow is None:
            update_message(user.user_id, 
                           message_id, 
                           "failed")
            raise HTTPException(status_code=500, detail="Error while processing the workflow.")
        
        url = f"{os.getenv('RUNPOD_DOMAIN')}/image-generation/"

        # Define the headers for the request
        headers = {
            'Content-Type': 'application/json'
        }

        # Define the payload for the request
        payload = {
            'workflow': workflow,
            'reference_image_url': settings.reference_image_url,
            'reference_image_path': reference_image_path,
            'controlnet_reference_image_url': settings.controlnet_reference_image_url,
            'controlnet_reference_image_path': controlnet_reference_image_path,
            'message_id': message_id,
            'user_id': user.user_id,
        }

        background_tasks.add_task(send_post_request, url, headers, payload)
    else:
        raise HTTPException(status_code=403, detail="Upgrade your plan to unlock permissions.")
    

def get_batch(user: Account) -> Optional[Message]:
    return data.get_batch(user.user_id)

def get_history(user: Account) -> Optional[List[Message]]:
    return data.get_history(user.user_id)