from pydantic import BaseModel

from typing import List, Optional
from datetime import datetime


class Settings(BaseModel):
    # Basic settings (mandatory)
    pos_prompt: Optional[str] = ""
    sampling_steps: Optional[int] = 40
    model: Optional[str] = "Realistic"
    width: Optional[int] = 1024
    height: Optional[int] = 1024
    n_images: Optional[int] = 1
    reference_image_url: Optional[str] = ""

    controlnet_enabled: Optional[bool] = False
    controlnet_model: Optional[str] = "Pose"
    controlnet_reference_image_url: Optional[str] = ""
    controlnet_strength: Optional[int] = 1
    controlnet_start_percent: Optional[int] = 60
    controlnet_end_percent: Optional[int] = 80

class Message(BaseModel):
    user_id: Optional[str] = None
    status: Optional[str] = None
    uploadcare_uris: Optional[List[str]] = None
    created_at: datetime | None = None
    message_id: Optional[str] = None
    s3_uris: Optional[List[str]] = None