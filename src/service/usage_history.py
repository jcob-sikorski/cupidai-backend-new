from fastapi import HTTPException

from typing import Optional

import data.usage_history as data

from model.account import Account
from model.usage_history import History


def update(domain: str, user_id: str) -> None:
    try:
        data.update(domain, user_id)
    except ValueError:
        raise ValueError("Failed to update the usage history.")


def get(user: Account) -> Optional[History]:
    try:
        return data.get(user.user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Failed to find usage history.")