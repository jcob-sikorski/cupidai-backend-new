from fastapi import HTTPException

import data.bug as data

from model.account import Account


def create(description: str, 
           user: Account) -> None:
    try:
        data.create(description, user.user_id)
    except ValueError:
        raise HTTPException(status_code=500, detail="Failed to report a bug.")