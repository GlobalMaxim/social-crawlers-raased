from pydantic import BaseModel, Field, constr
from datetime import datetime
from app.core.config import settings


class ProfileLanguageBase(BaseModel):
    language_name: constr(max_length=255)
    language_code: constr(max_length=10)

class ProfileLanguageCreate(ProfileLanguageBase):
    pass

class ProfileLanguageUpdate(ProfileLanguageBase):
    pass


class ProfileLanguageInDBBase(ProfileLanguageCreate):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    class Config:
        orm_mode = True


class ProfileLanguage(ProfileLanguageInDBBase):
    pass
