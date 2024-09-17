from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from app.core.config import settings
from pydantic import BaseModel, IPvAnyAddress, constr, conint, confloat


# Shared properties
class CookieBase(BaseModel):
    proxy_id:                   int | None = Field(
        title='Proxy ID', ge=1, le=settings.INT_MAX_SIZE)
    account_id:                 int = Field(
        title='Social Account ID', ge=1, le=settings.INT_MAX_SIZE)
    cookies_file:               constr(max_length=255)
    is_valid:                   bool = True
    is_locked: bool = False
    date_locked: datetime | None


class CookieCreate(CookieBase):
    created_at: datetime


class CookieUpdate(CookieBase):
    updated_at: Optional[datetime] = None


class CookieInDBBase(CookieBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


    class Config:
        orm_mode = True

class Cookie(CookieInDBBase):
    pass

