from datetime import datetime
from typing import List
from pydantic import BaseModel, HttpUrl, Field
from app.core.config import settings
from app.schemas.profile_language import ProfileLanguage
from app.schemas.profile_address import ProfileAddress
from app.schemas.profile_email import ProfileEmail
from app.schemas.profile_link import ProfileLink
from app.schemas.profile_messenger import ProfileMessenger
from app.schemas.profile_nickname import ProfileNickname
from app.schemas.profile_phone import ProfilePhone


class ProfileTask(BaseModel):
    profile_request_id:      int = Field(
        title='Profile request ID', ge=1, le=settings.INT_MAX_SIZE)
    external_id:            int = Field(
        title='External profile request ID', ge=1, le=settings.INT_MAX_SIZE)
    reply_link:                 HttpUrl
    first_name:                 str = None
    last_name:                  str = None
    date_of_birth:              datetime = None
    country_of_origin_code:     str = None
    country_of_residence_code:  str = None
    occupation:                 str = None
    social_links:               List[ProfileLink] = []
    youtube_links:              List[ProfileLink] = []
    web_links:                  List[ProfileLink] = []
    phones:                     List[ProfilePhone] = []
    addresses:                  List[ProfileAddress] = []
    emails:                     List[ProfileEmail] = []
    nicknames:                  List[ProfileNickname] = []
    languages:                  List[ProfileLanguage] = []
    messengers:                 List[ProfileMessenger] = []
    