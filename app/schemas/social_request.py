from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl, Field
from app.core.config import settings

from .social_keyword import SocialKeyword, SocialKeywordCreate
from .social_hashtag import SocialHashtag, SocialHashtagCreate
from .social_link import SocialLink, SocialLinkCreate

# Shared properties


class SocialRequestBase(BaseModel):
    external_id:               int = Field(
        default=None, title='External social request ID', ge=1, le=settings.INT_MAX_SIZE)
    active:                    bool
    is_global_search:          bool
    reply_link:                HttpUrl
    crawling_frequency:        int = Field(
        title='Crawling frequency in seconds', ge=0, le=settings.INT_MAX_SIZE)
    crawling_start_date:       datetime
    crawling_end_date:         datetime


class SocialRequestCreate(SocialRequestBase):
    social_keywords:           list[SocialKeywordCreate] = []
    social_hashtags:           list[SocialHashtagCreate] = []
    social_links:              list[SocialLinkCreate] = []


class SocialRequestUpdate(SocialRequestBase):
    crawling_last_run_date:    datetime | None = None


class SocialRequestInDBBase(SocialRequestBase):
    id: int
    crawling_last_run_date:    datetime | None = None
    social_keywords:           list[SocialKeyword] = []
    social_hashtags:           list[SocialHashtag] = []
    social_links:              list[SocialLink] = []
    created_at:                datetime
    updated_at:                datetime | None = None

    class Config:
        orm_mode = True


class SocialRequest(SocialRequestInDBBase):
    pass
