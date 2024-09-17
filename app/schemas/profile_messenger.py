from pydantic import BaseModel, Field, constr
from datetime import datetime
from app.core.config import settings


class ProfileMessengerBase(BaseModel):
    account: constr(max_length=255)
    messenger_name: constr(max_length=255)

class ProfileMessengerCreate(ProfileMessengerBase):
    created_at: datetime

class ProfileMessengerUpdate(ProfileMessengerBase):
    pass


class ProfileMessengerInDBBase(ProfileMessengerCreate):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        orm_mode = True


class ProfileMessenger(ProfileMessengerInDBBase):
    pass
