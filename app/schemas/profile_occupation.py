from pydantic import BaseModel, Field, constr
from datetime import datetime
from app.core.config import settings


class ProfileOccupationBase(BaseModel):
    name: constr(max_length=255)
    slug: constr(max_length=255)
    profile_request_id: int | None = Field(
        title='Profile Request ID', ge=1, le=settings.INT_MAX_SIZE)

class ProfileOccupationCreate(ProfileOccupationBase):
    created_at: datetime
    updated_at: datetime = None

class ProfileOccupationUpdate(ProfileOccupationBase):
    updated_at: datetime


class ProfileOccupationInDBBase(ProfileOccupationCreate):
    id: int

    class Config:
        orm_mode = True


class ProfileOccupation(ProfileOccupationInDBBase):
    pass
