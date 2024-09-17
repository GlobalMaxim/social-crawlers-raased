from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from app.core.config import settings


# Shared properties
class SocialKeywordBase(BaseModel):
    external_id:        int = Field(
        default=None, title='External social keyword ID', ge=1, le=settings.INT_MAX_SIZE)
    smm_engine_id:      int = Field(
        title='Social engine ID', ge=1, le=settings.INT_MAX_SIZE)
    keyword:            str
    operator:           str


class SocialKeywordCreate(SocialKeywordBase):
    pass


class SocialKeywordUpdate(SocialKeywordBase):
    pass


class SocialKeywordInDBBase(SocialKeywordBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None


    class Config:
        orm_mode = True


class SocialKeyword(SocialKeywordInDBBase):
    pass

