from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from app.core.config import settings


# Shared properties
class SocialPostAttachmentBase(BaseModel):
    social_parsing_post_id:   int | None = Field(
        title='Social parsing post ID', ge=1, le=settings.INT_MAX_SIZE)
    video_path:               str | None = None
    image_path:               str | None = None


class SocialPostAttachmentCreate(SocialPostAttachmentBase):
    pass


class SocialPostAttachmentUpdate(SocialPostAttachmentBase):
    external_id: int = Field(
        default=None, title='External social post ID', ge=1, le=settings.INT_MAX_SIZE)


class SocialPostAttachmentInDBBase(SocialPostAttachmentBase):
    id:                       int
    external_id:              int | None = Field(
        default=None, title='External social post ID', ge=1, le=settings.INT_MAX_SIZE)
    created_at:               datetime
    updated_at:               datetime | None = None

    class Config:
        orm_mode = True


class SocialPostAttachment(SocialPostAttachmentInDBBase):
    pass
