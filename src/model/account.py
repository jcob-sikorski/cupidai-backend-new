from pydantic import BaseModel

from datetime import datetime

class Account(BaseModel):
    user_id: str
    username: str
    password_hash: str | None = None
    email: str | None = None
    full_name: str | None = None
    profile_uri: str | None = None
    disabled: bool | None = None

class Invite(BaseModel):
    invite_id: str
    guest_id: str
    host_id: str
    signup_required: bool

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    # username: str | None = None
    # TODO: wht do we want to transport back to the user?

    pass

class PasswordReset(BaseModel):
    reset_id: str | None = None
    user_id: str | None = None
    email: str | None = None
    reset_link: str | None = None
    is_used: bool | None = None
    created_at: datetime | None = None