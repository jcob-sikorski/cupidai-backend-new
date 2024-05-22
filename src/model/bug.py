from pydantic import BaseModel

from datetime import datetime

class Bug(BaseModel):
    user_id: str | None = None
    created_at: datetime | None = None
    description: str | None = None