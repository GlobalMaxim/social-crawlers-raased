from typing import TypedDict
from pydantic import BaseModel, Field, constr
from datetime import datetime
from app.core.config import settings


class ProfileLinkBase(BaseModel):
    link: constr(max_length=255)
    smm_slug: constr(max_length=255) | None
class ProfileLinkCreate(ProfileLinkBase):
    pass

class ProfileLinkUpdate(ProfileLinkBase):
    pass


class ProfileLinkInDBBase(ProfileLinkCreate):
    id: int
    is_associative: bool | None = False
    # link_type: str | None
    created_at: datetime
    updated_at: datetime | None = None
    class Config:
        orm_mode = True

class ProfileLink(ProfileLinkInDBBase):
    pass