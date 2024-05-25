from typing import List, Optional

from datetime import datetime

from model.deepfake import Message

from pymongo import ReturnDocument, DESCENDING
from .init import deepfake_col


def create_message(user_id: Optional[str] = None,
           status: Optional[str] = None,
           facefusion_source_uris: Optional[List[str]] = None,
           facefusion_target_uri: Optional[str] = None,
           akool_source_uri: Optional[str] = None,
           akool_target_uri: Optional[str] = None,
           job_id: Optional[str] = None,
           output_url: Optional[str] = None) -> Optional[Message]:
    
    now = datetime.now()
    
    message = Message(
        user_id=user_id,
        status=status,
        facefusion_source_uris=facefusion_source_uris,
        facefusion_target_uri=facefusion_target_uri,
        akool_source_uri=akool_source_uri, 
        akool_target_uri=akool_target_uri,
        job_id=job_id,
        output_url=output_url,
        created_at=now
    )
    
    result = deepfake_col.insert_one(message.dict())
    if not result.inserted_id:
        raise ValueError("Failed to create message.")
    
    return message



def update_message(user_id: Optional[str] = None, 
                   status: Optional[str] = None,
                   facefusion_source_uris: Optional[List[str]] = None,
                   facefusion_target_uri: Optional[str] = None,
                   akool_source_uri: Optional[str] = None,
                   akool_target_uri: Optional[str] = None,
                   job_id: Optional[str] = None,
                   output_url: Optional[str] = None) -> Optional[str]:
    
    message = Message(
        user_id=user_id,
        status=status,
        facefusion_source_uris=facefusion_source_uris,
        facefusion_target_uri=facefusion_target_uri,
        akool_source_uri=akool_source_uri,
        akool_target_uri=akool_target_uri,
        job_id=job_id,
        output_url=output_url
    )

    update_fields = {key: value for key, value in message.dict().items() if value is not None}

    if job_id:
        deepfake_col.find_one_and_update(
            {"job_id": job_id},
            {"$set": update_fields},
            return_document=ReturnDocument.AFTER
        )
    else:
        message_id = deepfake_col.insert_one(update_fields)
        message_id = str(message_id.inserted_id)
    
        print("returning message_id")
        return message_id


def get_message(job_id: str) -> Optional[Message]:
    result = deepfake_col.find_one({"job_id": job_id})

    if result is not None:
        message = Message(**result)
        return message
    return None


def get_history(user_id: str) -> Optional[List[Message]]:
    results = deepfake_col.find({"user_id": user_id}).sort("created_at", DESCENDING)

    messages = [Message(**result) for result in results]

    return messages