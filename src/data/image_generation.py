from typing import List, Dict, Optional

from bson import ObjectId

from datetime import datetime

from model.image_generation import Settings, Message

from pymongo import ReturnDocument, DESCENDING
from .init import comfyui_col, settings_col

def update_message(user_id: str, 
                   status: Optional[str] = None, 
                   uploadcare_uris: Optional[List[str]] = None, 
                   message_id: Optional[str] = None, 
                   settings_id: Optional[str] = None, 
                   s3_uris: Optional[List[str]] = None) -> None:
    message = Message(
        user_id=user_id,
        status=status,
        uploadcare_uris=uploadcare_uris,
        message_id=message_id,
        settings_id=settings_id,
        s3_uris=s3_uris
    )

    # Only update created_at when status is 'started'
    if status == 'started':
        message.created_at = datetime.now()

    update_fields = {key: value for key, value in message.dict().items() if value is not None}

    if message_id:
        print("UPDATING MESSAGE (message_id not null)")
        comfyui_col.find_one_and_update(
            {"_id": ObjectId(message_id)},  # Convert message_id to ObjectId
            {"$set": update_fields},
            return_document=ReturnDocument.AFTER
        )
    else:
        print("CREATING NEW MESSAGE (message_id is null)")
        message_id = comfyui_col.insert_one(update_fields)
        message_id = str(message_id.inserted_id)
    
    return message_id


def save_settings(settings: Settings) -> None:
    result = settings_col.insert_one(settings.dict())
    inserted_id = str(result.inserted_id)
    return inserted_id


def get_batch(user_id: str) -> Optional[Message]:
    result = comfyui_col.find_one({"user_id": user_id}, sort=[("created_at", DESCENDING)])

    if result:
        message = Message(**result)
        return message
    else:
        return None