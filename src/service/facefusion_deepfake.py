from fastapi import HTTPException

from typing import List, Optional

import os

from uuid import uuid4

import requests

import data.deepfake as data

from model.account import Account
from model.deepfake import Message

import service.billing as billing_service
import service.deepfake as deepfake_service
import service.usage_history as usage_history_service

def webhook(response: dict) -> None:
    # TODO: update here the usage history
    data.update_message(job_id=response.job_id,
                        status=response.status)

def run_video_faceswap(source_uris: List[str],
                       target_uri: str,
                       user: Account) -> Optional[Message]:
    
    if billing_service.has_permissions("Realistic AI Content Deepfake", user):
        photo_file_formats = ['jpeg', 'png', 'heic']

        for source_uri in source_uris:
            deepfake_service.check_file_formats(source_uri, photo_file_formats)

        video_file_formats = ['mov', 'mp4', 'quicktime']

        deepfake_service.check_file_formats(target_uri, video_file_formats)

        url = f"{os.getenv('RUNPOD_DOMAIN')}/facefusion/"

        job_id = str(uuid4())

        # Define the headers for the request
        headers = {
            'Content-Type': 'application/json'
        }

        # Define the payload for the request
        payload = {
            'source_uris': source_uris,
            'target_uri': target_uri,
            'job_id': job_id,
            'user_id': user.user_id
        }

        requests.post(url, headers=headers, json=payload)

        return job_id
    else:
        raise HTTPException(status_code=403, detail="Upgrade your plan to unlock permissions.")