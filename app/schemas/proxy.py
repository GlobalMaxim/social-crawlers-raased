from pydantic import BaseModel, IPvAnyAddress, constr, conint, confloat
from datetime import datetime


class ProxyBase(BaseModel):
    username: constr(max_length=64) | None
    password: constr(max_length=64) | None
    ip: IPvAnyAddress
    port: conint(ge=0, le=65535)
    is_v6: bool | None
    is_valid: bool | None
    is_public: bool | None
    is_https: bool | None
    is_socks: bool | None
    is_anonymous: bool | None
    is_residential: bool | None
    is_datacenter: bool | None
    is_mobile: bool | None
    latency: confloat(ge=0.0) | None
    stability: confloat(ge=0.0) | None
    attempts: conint(ge=0) | None
    https_attempts: conint(ge=0) | None


class ProxyCreate(ProxyBase):
    created_at: datetime
    updated_at: datetime

class ProxyUpdate(ProxyBase):
    updated_at: datetime


class ProxyInDBBase(ProxyCreate):
    id: int

    class Config:
        orm_mode = True


class Proxy(ProxyInDBBase):
    pass
