from typing import List, Optional

import requests

import os

import time

import data.deepfake as data

from model.account import Account
from model.deepfake import Message

import service.billing as billing_service


def get_result(request_id) -> Optional[str]:
    print("GETTNG FACESWAP RESULT")
    for i in range(20):
        print(f"ITERATION {i} OF GETTING RESULT...")

        url = "https://faceswap3.p.rapidapi.com/result/"

        payload = { "request_id": request_id }
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
            "X-RapidAPI-Host": "faceswap3.p.rapidapi.com"
        }

        print("MAKING POST REQUEST...")
        response = requests.post(url, data=payload, headers=headers)

        response_data = response.json()

        print("RESPONSE FROM DEEPFAKE API: ", response_data)

        status = response_data.get("image_process_response", {}) \
                              .get("status", {})
        
        print("STATUS: ", status)

        if status == "Error":
            error_description = response_data.get("image_process_response", {}) \
                                             .get("description", {})
            raise ValueError(error_description)
        elif status == "OK":
            url = response_data.get("image_process_response", {}) \
                               .get("result_url", {})
    
            return url
        elif status == "InProgress":
            time.sleep(5)
        else:
            return None

    return None


def photo_faceswap(source_uri: str,
                   target_uri: str,
                   user: Account) -> Optional[Message]:
    
    if billing_service.has_permissions("Realistic AI Content Deepfake", user):
        print("MAKING PHOTO FACESWAP")

        print("SOURCE URI: ", source_uri)
        print("TARGET URI: ", target_uri)

        url = "https://faceswap3.p.rapidapi.com/faceswap/v1/image"

        payload = {
        	"swap_url": source_uri,
        	"target_url": target_uri
        }
        print(os.getenv("RAPIDAPI_KEY"))
        headers = {
        	"content-type": "application/x-www-form-urlencoded",
            "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        	"X-RapidAPI-Host": "faceswap3.p.rapidapi.com"
        }

        print("MAKING PHOTO FACESWAP POST REQUEST...")
        response = requests.post(url, data=payload, headers=headers)

        response_data = response.json()

        print("RESPONSE FROM PHOTO DEEPFAKE API: ", response_data)

        status = response_data.get("image_process_response", {}) \
                              .get("status", {})
        
        print("STATUS: ", status)

        if status == "Error":
            error_description = response_data.get("image_process_response", {}) \
                                             .get("description", {})
            raise ValueError(error_description)
        
        request_id = response_data.get("image_process_response", {}) \
                                  .get("request_id", {})

        output_url = get_result(request_id)

        print("GOT THE RESULT URL: ", output_url)

        message = create_message(user_id=user.user_id,
                                 status=status,
                                 source_uri=source_uri,
                                 target_uri=target_uri,
                                 type="photo",
                                 output_url=output_url)
        
        print("MESSAGE RETURNED ON PHOTO FACESWAP: ", message)

        return message


def video_faceswap(source_uri: str,
                   target_uuid: str,
                   target_filename: str,
                   user: Account) -> Optional[Message]:
    
    if billing_service.has_permissions("Realistic AI Content Deepfake", user):
        print("MAKING VIDEO FACESWAP")

        print("SOURCE URI: ", source_uri)
        print("TARGET UUID: ", target_uuid)
        print("TARGET FILENAME: ", target_filename)

        target_uri = f"https://ucarecdn.com/{target_uuid}/{target_filename}"

        url = "https://faceswap3.p.rapidapi.com/faceswap/v1/video"

        print(os.getenv("RAPIDAPI_KEY"))

        payload = {
            "swap_url": source_uri,
            "target_url": target_uri
        }
        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
            "X-RapidAPI-Host": "faceswap3.p.rapidapi.com"
        }

        print("PAYLOAD: ", payload)

        print("MAKING VIDEO FACESWAP POST REQUEST...")
        response = requests.post(url, data=payload, headers=headers)

        response_data = response.json()

        print("RESPONSE FROM VIDEO DEEPFAKE API: ", response_data)

        status = response_data.get("image_process_response", {}) \
                              .get("status", {})
        
        print("STATUS: ", status)

        if status == "Error":
            error_description = response_data.get("image_process_response", {}) \
                                             .get("description", {})
            raise ValueError(error_description)
        
        request_id = response_data.get("image_process_response", {}) \
                                  .get("request_id", {})

        output_url = get_result(request_id)

        print("GOT THE RESULT URL: ", output_url)

        message = create_message(user_id=user.user_id,
                                 status=status,
                                 source_uri=source_uri,
                                 target_uri=target_uri,
                                 type="video",
                                 output_url=output_url)
        
        print("MESSAGE RETURNED ON VIDEO FACESWAP: ", message)
        
        return message


def create_message(user_id: Optional[str] = None,
                   status: Optional[str] = None,
                   source_uri: Optional[str] = None,
                   target_uri: Optional[str] = None,
                   type: Optional[str] = None,
                   output_url: Optional[str] = None) -> Optional[Message]:
    
    return data.create_message(user_id,
                               status,
                               source_uri,
                               target_uri,
                               type,
                               output_url)

def get_message(job_id: str) -> Optional[Message]:
    return data.get_message(job_id)

def get_history(user: Account) -> Optional[List[Message]]:
    return data.get_history(user.user_id)