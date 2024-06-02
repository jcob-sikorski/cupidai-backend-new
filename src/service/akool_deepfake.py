from fastapi import HTTPException

from typing import Optional

import os

import json

import requests

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
      "webhookUrl": f"{os.getenv('ROOT_DOMAIN')}/akool-deepfake/webhook"
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
                                  akool_source_uri=source_uri,
                                  akool_target_uri=target_uri,
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