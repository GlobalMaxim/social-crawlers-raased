from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from app.core.config import settings


# Shared properties
class SocialPostRequestBase(BaseModel):
    social_parsing_post_id:     int | None = Field(
        title='Social parsing post ID', ge=1, le=settings.INT_MAX_SIZE)
    social_request_id:          int | None = Field(
        title='Social request ID', ge=1, le=settings.INT_MAX_SIZE)


class SocialPostRequestCreate(SocialPostRequestBase):
    pass


class SocialPostRequestUpdate(SocialPostRequestBase):
    external_id: int = Field(
        default=None, title='External social post ID', ge=1, le=settings.INT_MAX_SIZE)


class SocialPostRequestInDBBase(SocialPostRequestBase):
    id:                       int
    external_id:              int | None = Field(
        default=None, title='External social post ID', ge=1, le=settings.INT_MAX_SIZE)
    created_at:               datetime
    updated_at:               datetime | None = None

    class Config:
        orm_mode = True


class SocialPostRequest(SocialPostRequestInDBBase):
    pass
