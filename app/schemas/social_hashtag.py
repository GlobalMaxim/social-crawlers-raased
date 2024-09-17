from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from app.core.config import settings


# Shared properties
class SocialHashtagBase(BaseModel):
    external_id:        int = Field(
        default=None, title='External social hashtag ID', ge=1, le=settings.INT_MAX_SIZE)
    smm_engine_id:      int = Field(
        title='Social engine ID', ge=1, le=settings.INT_MAX_SIZE)
    hashtag:            str
    operator:           str


class SocialHashtagCreate(SocialHashtagBase):
    pass


class SocialHashtagUpdate(SocialHashtagBase):
    pass


class SocialHashtagInDBBase(SocialHashtagBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        orm_mode = True


class SocialHashtag(SocialHashtagInDBBase):
    pass
