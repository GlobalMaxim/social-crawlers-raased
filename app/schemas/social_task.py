from pydantic import BaseModel, HttpUrl, Field
from app.core.config import settings


class SocialTask(BaseModel):
    social_request_id:      int = Field(
        title='Social request ID', ge=1, le=settings.INT_MAX_SIZE)
    external_id:            int = Field(
        title='External social request ID', ge=1, le=settings.INT_MAX_SIZE)
    is_global_search:       bool
    smm_engine_id:          int = Field(
        title='Social engine ID', ge=1, le=settings.INT_MAX_SIZE)
    smm_engine_name:        str
    social_link:            str | None = None
    social_link_id:         int | None = Field(
        title='Social link ID', ge=1, le=settings.INT_MAX_SIZE)
    keyword:                str | None = None
    hashtag:                str | None = None
    reply_link:             HttpUrl
