from pydantic import BaseModel, IPvAnyAddress, constr
from datetime import datetime


class IPInfoBase(BaseModel):
    country: constr(max_length=64) | None
    country_iso: constr(min_length=2, max_length=3) | None = "en"
    region_code: constr(min_length=2, max_length=3) | None = "en"
    region_name: constr(max_length=64) | None
    city: constr(max_length=64) | None
    latitude: float | None
    longitude: float | None
    time_zone: constr(max_length=64) | None
    asn: constr(max_length=32) | None
    asn_org: constr(max_length=64) | None
    hostname: str | None


class IPInfoCreate(IPInfoBase):
    ip: IPvAnyAddress
    created_at: datetime


class IPInfoUpdate(IPInfoBase):
    updated_at: datetime


class IPInfoInDBBase(IPInfoCreate):
    updated_at: datetime
    id: int

    class Config:
        orm_mode = True


class IPInfo(IPInfoInDBBase):
    pass
