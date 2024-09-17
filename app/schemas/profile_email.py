from pydantic import BaseModel, Field, constr, EmailStr
from datetime import datetime
from app.core.config import settings


class ProfileEmailBase(BaseModel):
    email: EmailStr

class ProfileEmailCreate(ProfileEmailBase):
    created_at: datetime

class ProfileEmailUpdate(ProfileEmailBase):
    pass


class ProfileEmailInDBBase(ProfileEmailCreate):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    class Config:
        orm_mode = True


class ProfileEmail(ProfileEmailInDBBase):
    pass
