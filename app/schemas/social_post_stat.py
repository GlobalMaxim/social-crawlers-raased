from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from app.core.config import settings


# Shared properties
class SocialPostStatBase(BaseModel):
    social_parsing_post_id:     int | None = Field(
        title='Social parsing post ID', ge=1, le=settings.INT_MAX_SIZE)
    likes:                      int | None = Field(
        title='Likes count', ge=0, le=settings.INT_MAX_SIZE)
    comments:                   int | None = Field(
        title='Comments count', ge=0, le=settings.INT_MAX_SIZE)
    retweets:                   int | None = Field(
        title='Retweets count', ge=0, le=settings.INT_MAX_SIZE)
    subscribers:                int | None = Field(
        title='Subscribers count', ge=0, le=settings.INT_MAX_SIZE)


class SocialPostStatCreate(SocialPostStatBase):
    pass


class SocialPostStatUpdate(SocialPostStatBase):
    external_id:                int = Field(
        default=None, title='External social post ID', ge=1, le=settings.INT_MAX_SIZE)


class SocialPostStatInDBBase(SocialPostStatBase):
    id:                         int
    external_id:                int | None = Field(
        default=None, title='External social post ID', ge=1, le=settings.INT_MAX_SIZE)
    created_at:                 datetime
    updated_at:                 datetime | None = None

    class Config:
        orm_mode = True


class SocialPostStat(SocialPostStatInDBBase):
    pass
