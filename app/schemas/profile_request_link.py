from typing import TypedDict
from pydantic import BaseModel, Field, constr
from datetime import datetime
from app.core.config import settings
from .profile_link import ProfileLink


class ProfileRequestLinkBase(BaseModel):
    pass
    

class ProfileRequestLinkCreate(ProfileRequestLinkBase):
    social: list[ProfileLink]
    youtube: list[ProfileLink]
    web: list[ProfileLink]

class ProfileRequestLinkUpdate(ProfileRequestLinkBase):
    pass


class ProfileRequestLinkInDBBase(ProfileRequestLinkBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    profile_request_id: int 
    profile_link_id: int
    is_associative: bool | None = False
    link_type: constr(max_length=64)
    link: ProfileLink
    # social: list[ProfileLink]
    # youtube: list[ProfileLink]
    # web: list[ProfileLink]
    class Config:
        orm_mode = True


class ProfileRequestLink(ProfileRequestLinkInDBBase):
    pass