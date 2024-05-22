from model.bug import Bug

from .init import bug_col

from datetime import datetime


def create(description: str, 
           user_id: str) -> None:
    bug = Bug(user_id=user_id, description=description, created_at=datetime.now())

    result = bug_col.insert_one(bug.dict())

    if not result.inserted_id:
        raise ValueError("Failed to report a bug.")