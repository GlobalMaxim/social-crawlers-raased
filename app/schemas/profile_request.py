from typing import Any, List
from pydantic import BaseModel, Field, HttpUrl, constr
from datetime import datetime
from app.core.config import settings
from .profile_request_link import ProfileRequestLink, ProfileRequestLinkCreate
from .profile_address import ProfileAddressCreate, ProfileAddress
from .profile_email import ProfileEmail, ProfileEmailCreate
from .profile_language import ProfileLanguageCreate, ProfileLanguage
from .profile_link import ProfileLinkCreate
from .profile_messenger import ProfileMessengerCreate, ProfileMessenger
from .profile_nickname import ProfileNicknameCreate, ProfileNickname
from .profile_phone import ProfilePhoneCreate, ProfilePhone


class ProfileRequestBase(BaseModel):
    reply_link: HttpUrl
    external_id: int
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: datetime | None = None
    country_of_origin_code: constr(max_length=3) | None = None
    country_of_residence_code: constr(max_length=3) | None = None
    occupation: constr(max_length=64) | None = None
    is_active: bool = True

class ProfileRequestCreate(ProfileRequestBase):
    addresses: list | None = []
    emails: list | None = []
    languages: list | None = []
    links: dict | None = {}
    messengers: list | None = []
    nicknames: list | None= []
    phones: list | None = []
    updated_at: datetime | None = None

class ProfileRequestAppend(ProfileRequestCreate):
    reply_link: HttpUrl | None
    external_id: int | None


class ProfileRequestUpdate(ProfileRequestBase):
    last_autocomplete_date: datetime | None = None


class ProfileRequestInDBBase(ProfileRequestBase):
    id: int
    last_autocomplete_date: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    addresses: List[ProfileAddress] = []
    emails: list[ProfileEmail] = []
    languages: list[ProfileLanguage] = []
    requests_links: list[ProfileRequestLink] = []
    messengers: list[ProfileMessenger]  = []
    nicknames: list[ProfileNickname]  = []
    phones: list[ProfilePhone] = []

    class Config:
        orm_mode = True


class ProfileRequest(ProfileRequestInDBBase):
    pass
