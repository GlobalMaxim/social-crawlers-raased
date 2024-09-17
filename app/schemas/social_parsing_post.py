from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl, Field

from .social_post_request import SocialPostRequest, SocialPostRequestCreate
from .social_post_reaction import SocialPostReaction, SocialPostReactionCreate
from .social_post_attachment import SocialPostAttachment, SocialPostAttachmentCreate
from .social_post_stat import SocialPostStat, SocialPostStatCreate
from app.core.config import settings


# Shared properties
class SocialParsingPostBase(BaseModel):
    social_request_id:      int = Field(
        title='Social request ID', ge=1, le=settings.INT_MAX_SIZE)
    link_id:                Optional[int] = Field(
        default=None, title='Social link ID', ge=1, le=settings.INT_MAX_SIZE)
    smm_id:                 Optional[int] = Field(
        default=None, title='SMM ID', ge=1, le=settings.INT_MAX_SIZE)
    account_name:           str | None = None
    account_login:          str | None = None
    post_name:              str | None = None
    title:                  str | None = None
    description:            str | None = None
    content:                str | None = None
    featured_image:         str | None = None
    video_image:            str | None = None
    is_storie:              bool = False
    source_link:            HttpUrl | None = None
    is_updated:             bool = False
    crawler_name:           str | None = None
    date_of_news:           datetime | None = None


class SocialParsingPostCreate(SocialParsingPostBase):
    social_posts_attachments:     list[SocialPostAttachmentCreate] = []
    social_posts_reactions:       list[SocialPostReactionCreate] = []
    social_posts_stats:           SocialPostStatCreate | None = None


class SocialParsingPostUpdate(SocialParsingPostBase):
    external_id:              int | None = Field(
        default=None, title='External social post ID', ge=1, le=settings.INT_MAX_SIZE)


class SocialParsingPostInDBBase(SocialParsingPostBase):
    id:                       int
    external_id:              int | None = Field(
        default=None, title='External social post ID', ge=1, le=settings.INT_MAX_SIZE)
    social_posts_attachments: list[SocialPostAttachment] = []
    social_posts_reactions:   list[SocialPostReaction] = []
    social_posts_stats:       SocialPostStat | None = None
    social_posts_requests:    list[SocialPostRequest] = []
    created_at:               datetime
    updated_at:               datetime | None = None

    class Config:
        orm_mode = True


class SocialParsingPost(SocialParsingPostInDBBase):
    pass
