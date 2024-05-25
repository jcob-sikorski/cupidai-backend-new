from pydantic import BaseModel, Field
from typing import Optional, List

from datetime import datetime

class Message(BaseModel):
    user_id: Optional[str] = None, 
    status: Optional[str] = None
    facefusion_source_uris: Optional[List[str]] = None
    facefusion_target_uri: Optional[str] = None
    akool_source_uri: Optional[str] = None
    akool_target_uri: Optional[str] = None
    job_id: Optional[str] = None
    output_url: Optional[str] = None
    created_at: datetime | None = None