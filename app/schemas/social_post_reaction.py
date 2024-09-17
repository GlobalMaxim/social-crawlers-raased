from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
import pydantic
from app.core.config import settings
from enum import Enum

class ReactionType(str, Enum):
    LIKE = 'LIKE'
    CARE = 'CARE'
    LOVE = 'LOVE'
    HAHA = 'HAHA'
    SAD = 'SAD'
    ANGRY = 'ANGRY'
    WOW = 'WOW'

# Shared properties
class SocialPostReactionBase(BaseModel):
    social_parsing_post_id:     int | None = Field(
        title='Social parsing post ID', ge=1, le=settings.INT_MAX_SIZE)
    reaction:                   ReactionType | None = None
    count:                      int | None = Field(
        title='Reaction count', ge=0, le=settings.INT_MAX_SIZE)
    @pydantic.validator('reaction', pre=True)
    def validate_enum_field(cls, reaction: str):
        return ReactionType(reaction)


class SocialPostReactionCreate(SocialPostReactionBase):
    pass


class SocialPostReactionUpdate(SocialPostReactionBase):
    external_id:                int = Field(
        default=None, title='External social post ID', ge=1, le=settings.INT_MAX_SIZE)


class SocialPostReactionInDBBase(SocialPostReactionBase):
    id:                         int
    external_id:                int | None = Field(
        default=None, title='External social post ID', ge=1, le=settings.INT_MAX_SIZE)
    created_at:                 datetime
    updated_at:                 datetime | None = None

    class Config:
        orm_mode = True


class SocialPostReaction(SocialPostReactionInDBBase):
    pass
