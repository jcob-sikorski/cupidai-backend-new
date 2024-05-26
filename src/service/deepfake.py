from fastapi import HTTPException

from typing import List, Optional

import os

import re

from pyuploadcare import Uploadcare

import data.deepfake as data

from model.account import Account
from model.deepfake import Message

def get_file_format(file_id: str):
    uploadcare = Uploadcare(public_key=os.getenv('UPLOADCARE_PUBLIC_KEY'), 
                            secret_key=os.getenv('UPLOADCARE_SECRET_KEY'))

    file_info = uploadcare.file(file_id).info

    return file_info['mime_type'].split('/')[1]

def extract_id_from_uploadcare_uri(uploadcare_uri):
    # Use regex to extract the UUID from the URI
    match = re.search(r"/([a-f0-9-]+)/", uploadcare_uri)
    if match:
        return match.group(1)
    else:
        return None

def check_file_formats(uploadcare_uri, valid_formats):
    file_id = extract_id_from_uploadcare_uri(uploadcare_uri)
    file_format = get_file_format(file_id)

    print("FILE FORMAT: ", file_format)

    if file_format not in valid_formats:

        raise HTTPException(status_code=400, detail=f"Invalid file format. \
                            Valid ones are {valid_formats}")
    
def get_file_formats(uploadcare_uris):
    file_formats = []

    for uri in uploadcare_uris:
        file_id = extract_id_from_uploadcare_uri(uri)
        file_format = get_file_format(file_id)

        file_formats.append(file_format)

    return file_formats

def get_message(job_id: str) -> Optional[Message]:
    return data.get_message(job_id)

def get_history(user: Account) -> Optional[List[Message]]:
    return data.get_history(user.user_id)