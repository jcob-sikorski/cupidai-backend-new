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
import service.deepfake as deepfake_service
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


def decipher_status_message(status_code: int) -> str:
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
        status_msg = decipher_status_message(status_code)

        job_id = result.get("_id", "")

        data.update_message(job_id=job_id,
                            status=status_msg)

    else:
        raise ValueError("Invalid signature.")
    

def initiate_photo_faceswap(source_uri: str,
                            target_uri: str,
                            user: Account) -> Optional[Message]:
    
    if billing_service.has_permissions("Realistic AI Content Deepfake", user):
        valid_formats = ['jpeg', 'png']

        deepfake_service.check_file_formats(target_uri,
                                            valid_formats)
        deepfake_service.check_file_formats(source_uri,
                                            valid_formats)
                       
        source_opts = face_detect(source_uri)
        target_opts = face_detect(target_uri)
          
        try:
            message = run_photo_faceswap(source_uri,
                                         target_uri,
                                         source_opts,
                                         target_opts,
                                         user.user_id)

            return message
        except ValueError:
            raise HTTPException(status_code=400, detail="Failed to generate a photo deepfake.")
    else:
        raise HTTPException(status_code=403, detail="Upgrade your plan to unlock permissions.")
    

def initiate_video_faceswap(source_uri: str,
                            target_uri: str,
                            video_uri: str,
                            user: Account) -> Optional[Message]:
    
    if billing_service.has_permissions("Realistic AI Content Deepfake", user):
        # valid_formats = ['jpeg', 'png', 'mp4']

        # deepfake_service.check_file_formats(target_uri,
        #                                     valid_formats)
        # deepfake_service.check_file_formats(source_uri,
        #                                     valid_formats)
        
        # deepfake_service.check_file_formats(video_uri,
        #                                     valid_formats)

        print("INITIATING VIDEO FACESWAP")
                       
        source_opts = face_detect(source_uri)
        target_opts = face_detect(target_uri)

        print("DETECTED FACES")
          
        try:
            message = run_video_faceswap(source_uri,
                                         target_uri,
                                         video_uri,
                                         source_opts,
                                         target_opts,
                                         user.user_id)

            return message
        except ValueError:
            raise HTTPException(status_code=400, detail="Failed to generate a video deepfake.")
    else:
        raise HTTPException(status_code=403, detail="Upgrade your plan to unlock permissions.")

    
def run_photo_faceswap(source_uri: str, # photo of the old face from the photo
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

    print("SENDING REQUEST TO AKOOL")
    try:
        message = send_post_request(url,
                                    headers,
                                    payload,
                                    source_uri,
                                    target_uri,
                                    user_id)
        
        return message
    except ValueError:
        raise HTTPException(status_code=400, 
                            detail="Failed to generate photo deepfake.")
    

def run_video_faceswap(source_uri: str, # photo of the old face from the photo
                       target_uri: str, # photo of the new face for the photo
                       video_uri: str,
                       source_opts: str, # some params for the old face
                       target_opts: str, # some params for the new face
                       user_id: str) -> Optional[Message]:
    
    print("RUNNING VIDEO FACESWAP")
    url = "https://openapi.akool.com/api/open/v3/faceswap/highquality/specifyvideo"

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
      "modifyVideo": video_uri, # photo to modify
      "webhookUrl": f"{os.getenv('ROOT_DOMAIN')}/deepfake/webhook"
    }

    print("SENDING REQUEST TO AKOOL")
    try:
        message = send_post_request(url,
                                    headers,
                                    payload,
                                    source_uri,
                                    target_uri,
                                    user_id)
        
        return message
    except ValueError:
        raise HTTPException(status_code=400, 
                            detail="Failed to generate video deepfake.")
    

def send_post_request(url: str, 
                      headers: dict, 
                      payload: dict,
                      source_uri: str,
                      target_uri: str,
                      user_id: str) -> Optional[Message]:
    print("SENDING POST REQUEST")
    response = requests.post(url, headers=headers, json=payload)

    response_data = response.json()  # Convert response to JSON

    print("RESPONSE FROM AKOOL: ", response_data)

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
                                  job_id=job_id,
                                  output_url=output_url)
        
    
    usage_history_service.update('deepfake', user_id)

    return message


def face_detect(uploadcare_uri: str):
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


def get_file_format(file_id: str):
    print("GETTING FILE FORMAT")
    print(file_id)
    uploadcare = Uploadcare(public_key=os.getenv('UPLOADCARE_PUBLIC_KEY'), 
                            secret_key=os.getenv('UPLOADCARE_SECRET_KEY'))

    file_info = uploadcare.file(file_id).info

    return file_info['mime_type'].split('/')[1]


def extract_id_from_uploadcare_uri(uploadcare_uri):
    print("EXTRACTING ID FROM UPLODCARE URI")
    print(uploadcare_uri)
    # Use regex to extract the UUID from the URI
    match = re.search(r"/([a-f0-9-]+)/", uploadcare_uri)
    if match:
        return match.group(1)
    else:
        return None


def check_file_formats(uploadcare_uri, valid_formats):
    print("CHECKING FILE FORMATS")
    file_id = extract_id_from_uploadcare_uri(uploadcare_uri)
    file_format = get_file_format(file_id)

    print("FILE FORMAT: ", file_format)

    if file_format not in valid_formats:

        raise HTTPException(status_code=400, detail=f"Invalid file format. \
                            Valid ones are {valid_formats}")
    

def get_file_formats(uploadcare_uris):
    print("GETTINGS FILE FORMATS FROM LIST")
    file_formats = []

    for uri in uploadcare_uris:
        file_id = extract_id_from_uploadcare_uri(uri)
        file_format = get_file_format(file_id)

        if file_format == "quicktime":
            file_format = "mp4"

        file_formats.append(file_format)

    print("FILE FORMATS: ", file_formats)

    return file_formats


def create_message(user_id: Optional[str] = None,
                   status: Optional[str] = None,
                   source_uri: Optional[str] = None,
                   target_uri: Optional[str] = None,
                   job_id: Optional[str] = None,
                   output_url: Optional[str] = None) -> Optional[Message]:
    
    return data.create_message(user_id,
                               status,
                               source_uri,
                               target_uri,
                               job_id,
                               output_url)


def get_message(job_id: str) -> Optional[Message]:
    return data.get_message(job_id)


def get_history(user: Account) -> Optional[List[Message]]:
    return data.get_history(user.user_id)