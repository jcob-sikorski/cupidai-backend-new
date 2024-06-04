from pydantic import BaseModel
from typing import Optional

from datetime import datetime

class Message(BaseModel):
    user_id: Optional[str] = None, 
    status: Optional[str] = None
    source_uri: Optional[str] = None
    target_uri: Optional[str] = None
    output_url: Optional[str] = None
    type: Optional[str] = None
    created_at: datetime | None = None