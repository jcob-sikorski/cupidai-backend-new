from typing import Optional, List

import data.midjourney as data
from data.midjourney import Message

from model.account import Account


def webhook(message: Message) -> None:
    data.update(message)

def valid_button(messageId: str, 
                 button: str) -> bool:
    return data.valid_button(messageId, 
                             button)

def get_message(messageId: str) -> Optional[Message]:
    return data.get_message(messageId)

def get_history(user: Account) -> List[Message]:
    return data.get_history(user.user_id)