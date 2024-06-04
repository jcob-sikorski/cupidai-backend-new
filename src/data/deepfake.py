from typing import List, Optional

from datetime import datetime

from model.deepfake import Message

from pymongo import DESCENDING
from .init import deepfake_col


def create_message(user_id: Optional[str] = None,
                   status: Optional[str] = None,
                   source_uri: Optional[str] = None,
                   target_uri: Optional[str] = None,
                   type: Optional[str] = None,
                   output_url: Optional[str] = None) -> Optional[Message]:
    
    now = datetime.now()
    
    message = Message(
        user_id=user_id,
        status=status,
        source_uri=source_uri,
        target_uri=target_uri,
        output_url=output_url,
        type=type,
        created_at=now
    )

    result = deepfake_col.insert_one(message.dict())
    if not result.inserted_id:
        raise ValueError("Failed to create message.")
    
    return message


def get_history(user_id: str) -> Optional[List[Message]]:
    results = deepfake_col.find({"user_id": user_id}).sort("created_at", DESCENDING)

    messages = [Message(**result) for result in results]

    return messages