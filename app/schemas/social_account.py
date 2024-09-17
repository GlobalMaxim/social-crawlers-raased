from datetime import datetime
from typing import Optional
from pydantic import BaseModel, IPvAnyAddress, constr, conint, confloat
from pydantic import BaseModel, Field
from app.core.config import settings
from enum import Enum

class Gender(Enum):
    M = 'M'
    F = 'F'
    O = 'O'

# Shared properties
class SocialAccountBase(BaseModel):
    smm_id:      int = Field(
        title='Social engine ID', ge=1, le=settings.INT_MAX_SIZE) 
    login:                      constr(max_length=64) | None 
    email:                      constr(max_length=64) | None
    email_password:             constr(max_length=64) | None
    password:                   constr(max_length=64) | None
    phone:                      constr(max_length=64) | None
    first_name:                 constr(max_length=64) | None
    last_name:                  constr(max_length=64) | None
    gender:                     Gender 
    country_iso:                constr(max_length=2) | None = "en"
    language_iso:               constr(max_length=2) | None = "en"
    is_active:                  bool = True
    is_twofactor:               bool = False
    twofactor_token:            constr(max_length=64) | None
    twofactor_recovery_codes:   constr(max_length=64) | None
    user_agent:                 constr(max_length=255) | None
    bans_count:                 conint() = 0
    captcha_count:              conint() = 0
    quality_percent:            confloat() = 50.0


class SocialAccountCreate(SocialAccountBase):
    created_at: datetime


class SocialAccountUpdate(SocialAccountBase):
    updated_at: Optional[datetime] = None


class SocialAccountInDBBase(SocialAccountBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


    class Config:
        orm_mode = True


class SocialAccount(SocialAccountInDBBase):
    pass

