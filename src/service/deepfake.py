from fastapi import HTTPException

from typing import List, Optional

import os

import re

from pyuploadcare import Uploadcare

import data.deepfake as data

from model.account import Account
from model.deepfake import Message

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

    return file_formats

def create_message(user_id: Optional[str] = None,
                   status: Optional[str] = None,
                   facefusion_source_uris: Optional[List[str]] = None,
                   facefusion_target_uri: Optional[str] = None,
                   akool_source_uri: Optional[str] = None,
                   akool_target_uri: Optional[str] = None,
                   job_id: Optional[str] = None,
                   output_url: Optional[str] = None) -> Optional[Message]:
    
    return data.create_message(user_id,
                          status,
                          facefusion_source_uris,
                          facefusion_target_uri,
                          akool_source_uri,
                          akool_target_uri,
                          job_id,
                          output_url)

def get_message(job_id: str) -> Optional[Message]:
    return data.get_message(job_id)

def get_history(user: Account) -> Optional[List[Message]]:
    return data.get_history(user.user_id)