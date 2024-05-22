from pydantic import BaseModel, Field
from typing import Optional, List

from datetime import datetime

class Message(BaseModel):
    user_id: Optional[str] = None, 
    status: Optional[str] = None
    source_uri: Optional[str] = None
    target_uri: Optional[str] = None
    modify_video: Optional[str] = None
    job_id: Optional[str] = None
    output_url: Optional[str] = None
    created_at: datetime | None = None