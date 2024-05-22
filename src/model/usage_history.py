from pydantic import BaseModel
from typing import Optional

class History(BaseModel):
    user_id: str
    images_generated: Optional[int] = None
    deepfakes_generated: Optional[int] = None
    ai_verification_generated: Optional[int] = None
    content_utilities_used: Optional[int] = None
    people_referred: Optional[int] = None
