from pydantic import BaseModel, Field, constr
from datetime import datetime
from app.core.config import settings


class ProfilePhoneBase(BaseModel):
    number: str

class ProfilePhoneCreate(ProfilePhoneBase):
    created_at: datetime

class ProfilePhoneUpdate(ProfilePhoneBase):
    pass


class ProfilePhoneInDBBase(ProfilePhoneCreate):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    class Config:
        orm_mode = True


class ProfilePhone(ProfilePhoneInDBBase):
    pass
