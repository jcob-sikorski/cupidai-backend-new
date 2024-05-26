from fastapi import BackgroundTasks, HTTPException

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

def webhook(message: Message) -> None:
    data.update_message(user_id=message.user_id,
                        job_id=message.job_id,
                        status=message.status,
                        output_url=message.output_url)
    
    if message.status == 'completed':
        usage_history_service.update('deepfake', message.user_id)

def send_post_request(url: str, headers: dict, payload: dict) -> None:
    requests.post(url, headers=headers, json=payload)

def run_video_faceswap(source_uris: str,
                       target_uri: str,
                       user: Account,
                       background_tasks: BackgroundTasks) -> str:
    
    if billing_service.has_permissions("Realistic AI Content Deepfake", user):
        print("RUNNING VIDEO FACESWAP")
        photo_file_formats = ['jpeg', 'png', 'heic']

        source_uris = [source_uris]
        
        print('CHECKING PHOTO FILE FORMATS')
        for source_uri in source_uris:
            deepfake_service.check_file_formats(source_uri, photo_file_formats)

        video_file_formats = ['mov', 'mp4', 'quicktime']

        print('CHECKING VIDEO FILE FORMATS')
        deepfake_service.check_file_formats(target_uri, video_file_formats)

        print('GETTING FILE FORMATS')
        file_formats = deepfake_service.get_file_formats(source_uris+[target_uri])

        print("FILE FORMATS: ", file_formats)

        url = f"{os.getenv('RUNPOD_DOMAIN')}/facefusion/"

        job_id = str(uuid4())

        print("CREATING A MESSAGE")
        deepfake_service.create_message(user_id=user.user_id, 
                                        status="started", 
                                        facefusion_source_uris=source_uris,
                                        facefusion_target_uri=target_uri,
                                        job_id=job_id,
                                        output_url=None)

        # Define the headers for the request
        headers = {
            'Content-Type': 'application/json'
        }

        # Define the payload for the request
        payload = {
            'source_uris': source_uris,
            'target_uri': target_uri,
            'job_id': job_id,
            'file_formats': file_formats,
            'user_id': user.user_id
        }

        background_tasks.add_task(send_post_request, url, headers, payload)

        return job_id
    else:
        raise HTTPException(status_code=403, 
                            detail="Upgrade your plan to unlock permissions.")