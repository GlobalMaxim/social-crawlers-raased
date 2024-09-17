from pydantic import BaseModel, Field, constr
from datetime import datetime
from app.core.config import settings


class ProfileAddressBase(BaseModel):
    address: constr(max_length=255) | None

class ProfileAddressCreate(ProfileAddressBase):
    created_at: datetime

class ProfileAddressUpdate(ProfileAddressBase):
    pass


class ProfileAddressInDBBase(ProfileAddressCreate):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        orm_mode = True


class ProfileAddress(ProfileAddressInDBBase):
    pass
