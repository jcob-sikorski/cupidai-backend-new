from pydantic import BaseModel, Field
from typing import List, Optional

class Message(BaseModel):
    messageId: Optional[str] = None
    prompt: Optional[str] = None
    uri: Optional[str] = None
    progress: Optional[int] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    buttons: Optional[List[str]] = None
    originatingMessageId: Optional[str] = None
    ref: Optional[str] = None
    error: Optional[str] = None

class Response(BaseModel):
    success: bool
    messageId: Optional[str] = None
    createdAt: Optional[str] = None
    error: Optional[str] = None