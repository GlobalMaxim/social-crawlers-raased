from pydantic import BaseModel, Field, constr
from datetime import datetime
from app.core.config import settings


class ProfileNicknameBase(BaseModel):
    nickname: constr(max_length=255)

class ProfileNicknameCreate(ProfileNicknameBase):
    pass

class ProfileNicknameUpdate(ProfileNicknameBase):
    pass


class ProfileNicknameInDBBase(ProfileNicknameCreate):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    class Config:
        orm_mode = True


class ProfileNickname(ProfileNicknameInDBBase):
    pass
