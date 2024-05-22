from typing import List, Optional

from model.midjourney import Message

from pymongo import ReturnDocument
from .init import midjourney_col


def update(message: Message) -> None:
    midjourney_col.find_one_and_update(
        {"messageId": message.messageId},
        {"$set": message.dict()},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )

def valid_button(messageId: str,
                 button: str) -> bool:
    print("VALIDATING ACTION")
    result = midjourney_col.find_one({"messageId": messageId})

    if result is not None:
        message = Message(**result)
        
        return button in message.buttons
    
    return False

def get_message(messageId: str) -> Optional[Message]:
    print("GETTING MESSAGE")
    result =  midjourney_col.find_one({"messageId": messageId})

    if result is not None:
        message = Message(**result)
        return message
    return None

def get_history(user_id: str) -> List[Message]:
    results = midjourney_col.find({"ref": user_id})

    messages = [Message(**result) for result in results]
    print(messages)

    return messages[::-1]