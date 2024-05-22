from fastapi import HTTPException

from typing import List, Optional

import os

import re

import json

import requests

from pyuploadcare import Uploadcare

import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64

import data.deepfake as data

from model.account import Account
from model.deepfake import Message

import service.billing as billing_service
import service.usage_history as usage_history_service

# Generate signature
def generate_msg_signature(client_id, 
                           timestamp, 
                           nonce, 
                           msg_encrypt):
    sorted_str = ''.join(sorted([client_id, str(timestamp), str(nonce), msg_encrypt]))

    hash_obj = hashlib.sha1(sorted_str.encode())
    
    return hash_obj.hexdigest()

# Decryption algorithm
def generate_aes_decrypt(data_encrypt, 
                         client_id, 
                         client_secret) -> dict:
    aes_key = client_secret.encode()

    # Ensure IV is 16 bytes long
    iv = client_id.encode()[:16]

    cipher = AES.new(aes_key, AES.MODE_CBC, iv)

    decrypted = unpad(cipher.decrypt(base64.b64decode(data_encrypt)), AES.block_size)

    return decrypted.decode()

def status_message(status_code: int) -> str:
    if status_code == 1 or status_code == 2:
        return "in progress"
    elif status_code == 3:
        return "completed"
    elif status_code == 4:
        return "failed"
    else:
        return "unknown"

def webhook(response: dict) -> None:
    clientId = os.getenv('AKOOL_CLIENT_ID')
    clientSecret = os.getenv('AKOOL_CLIENT_SECRET')

    signature = response["signature"]
    msg_encrypt = response["dataEncrypt"]
    timestamp = response["timestamp"]
    nonce = response["nonce"]

    new_signature = generate_msg_signature(clientId, timestamp, nonce, msg_encrypt)
    if signature == new_signature:
        result = generate_aes_decrypt(msg_encrypt, clientId, clientSecret)
        result = json.loads(result)

        print(f"AKOOL RESULT: {result}")
        
        # # Extracting status code and generating status message
        status_code = result.get("status", 0)
        status_msg = status_message(status_code)

        job_id = result.get("_id", "")

        data.update_message(job_id=job_id,
                            status=status_msg)

    else:
        raise ValueError("Invalid signature.")

def send_post_request(url: str, 
                      headers: dict, 
                      payload: dict,
                      source_uri: str,
                      target_uri: str,
                      modify_video: str,
                      user_id: str) -> Optional[Message]:
    response = requests.post(url, headers=headers, json=payload)

    response_data = response.json()  # Convert response to JSON

    print(response_data)

    code = response_data.get("code")

    if code != 1000:
        raise ValueError("There was an error in a post request.")

    response_data = response_data.get("data", {})

    job_id = response_data.get("_id")

    output_url = response_data.get("url")

    message = data.create_message(user_id=user_id,
                        status='in progress' if code == 1000 else 'failed',
                        source_uri=source_uri,
                        target_uri=target_uri,
                        modify_video=modify_video,
                        job_id=job_id,
                        output_url=output_url)
        
    
    usage_history_service.update('deepfake', user_id)

    return message

def extract_id_from_uri(uri):
    # Use regex to extract the UUID from the URI
    match = re.search(r"/([a-f0-9-]+)/", uri)
    if match:
        return match.group(1)
    else:
        return None

def get_file_format(file_id: str):
    uploadcare = Uploadcare(public_key=os.getenv('UPLOADCARE_PUBLIC_KEY'), secret_key=os.getenv('UPLOADCARE_SECRET_KEY'))

    file_info = uploadcare.file(file_id).info

    return file_info['mime_type'].split('/')[1]

def run_face_detection(uploadcare_uri: str):
    url = "https://sg3.akool.com/detect"

    payload = json.dumps({
      "single_face": True,
      "image_url": uploadcare_uri
    })
    headers = {
      'Authorization': 'Bearer token',
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response_data = json.loads(response.text)

    landmarks_str = response_data.get("landmarks_str", "")

    return landmarks_str

def run_photo(source_uri: str, # photo of the old face from the photo
              target_uri: str, # photo of the new face for the photo
              source_opts: str, # some params for the old face
              target_opts: str, # some params for the new face
              user_id: str) -> Optional[Message]:
    url = "https://openapi.akool.com/api/open/v3/faceswap/highquality/specifyimage"

    headers = {
      'Authorization': f"Bearer {os.getenv('AKOOL_ACCESS_TOKEN')}",
      'Content-Type': 'application/json'
    }

    payload = {
      "sourceImage": [{ # array of new faces
            "path": source_uri,
            "opts": source_opts
        },],
      "targetImage": [{ # array of old faces
            "path": target_uri,
            "opts": target_opts
        },],
      "face_enhance": 1,
      "modifyImage": target_uri, # photo to modify
      "webhookUrl": f"{os.getenv('ROOT_DOMAIN')}/deepfake/webhook"
    }

    try:
        message = send_post_request(url,
                                   headers,
                                   payload,
                                   source_uri,
                                   target_uri,
                                   None,
                                   user_id)
        
        return message
    except ValueError:
        raise HTTPException(status_code=400, detail="Failed to generate a deepfake.")

# TODO: we're providing to small amount of faces for the video - because there's a change it will interpret the video as multiface with even single face
# there's a possiblity that we should provide the url to the run face detection and check the mutliface to true
# get the array and pass it to the run_video

# TODO: figure out how to fix the "failed" error from the API
def run_video(source_uri: str, # photo of the old face from the photo
              target_uri: str, # photo of the new face for the photo
              source_opts: str, # some params for the old face
              target_opts: str, # some params for the new face
              modify_video: str, # video to modify
              user_id: str) -> Optional[Message]:
    url = "https://openapi.akool.com/api/open/v3/faceswap/highquality/specifyvideo"

    headers = {
      'Authorization': f"Bearer {os.getenv('AKOOL_ACCESS_TOKEN')}",
      'Content-Type': 'application/json'
    }

    payload = {
      "sourceImage": [{ # array of new faces
            "path": source_uri,
            "opts": source_opts
        }],
      "targetImage": [{ # array of old faces
            "path": target_uri,
            "opts": target_opts
        }],
      "face_enhance": 1,
      "modifyVideo": modify_video, # video to modify
      "webhookUrl": f"{os.getenv('ROOT_DOMAIN')}/deepfake/webhook"
    }

    try:
        message = send_post_request(url,
                                   payload,
                                   headers,
                                   source_uri,
                                   target_uri,
                                   modify_video,
                                   user_id)
        
        return message
    except ValueError:
        raise HTTPException(status_code=400, detail="Failed to generate a deepfake.")

# TODO: if the uploaded file is a video there must be toggle button
# if the video is running then there are three areas to drag and drop:
# first is for source image, second is for target image and third is for video


def generate(source_uri: str,
             target_uri: str,
             modify_video: str,
             user: Account) -> Optional[Message]:
    
    if billing_service.has_permissions("Realistic AI Content Deepfake", user):
        source_id = extract_id_from_uri(source_uri)
        source_format = get_file_format(source_id)

        target_id = extract_id_from_uri(target_uri)
        target_format = get_file_format(target_id)

        if source_format not in ['jpeg', 'png', 'heic'] or \
           target_format not in ['jpeg', 'png', 'heic']:

            raise HTTPException(status_code=400, detail="Invalid source/target format. Valid ones are jpeg, png, heic.")
            
        if modify_video:
            video_id = extract_id_from_uri(modify_video)

            video_format = get_file_format(video_id)

            if video_format not in ['mov', 'mp4', 'quicktime']:
                raise HTTPException(status_code=400, detail="Invalid video format. Valid ones are mov, mp4, quicktime.")

            source_opts = run_face_detection(source_uri)
            target_opts = run_face_detection(target_uri)

            try:
                message = run_video(source_uri,
                                   target_uri,
                                   source_opts,
                                   target_opts,
                                   modify_video,
                                   user.user_id)
                
                return message
            except ValueError:
                raise HTTPException(status_code=400, detail="Failed to generate a deepfake.")
        else:            
            source_opts = run_face_detection(source_uri)
            target_opts = run_face_detection(target_uri)
          
            try:
                message = run_photo(source_uri,
                                   target_uri,
                                   source_opts,
                                   target_opts,
                                   user.user_id)

                return message
            except ValueError:
                raise HTTPException(status_code=400, detail="Failed to generate a deepfake.")
    else:
        raise HTTPException(status_code=403, detail="Upgrade your plan to unlock permissions.")

def get_message(job_id: str) -> Optional[Message]:
    return data.get_message(job_id)

def get_history(user: Account) -> Optional[List[Message]]:
    return data.get_history(user.user_id)