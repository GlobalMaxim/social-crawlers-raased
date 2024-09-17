from typing import Optional

from pydantic import BaseModel, EmailStr


# Shared properties
class ApiUserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    full_name: Optional[str] = None


# Properties to receive via API on creation
class ApiUserCreate(ApiUserBase):
    email: EmailStr
    password: str


# Properties to receive via API on update
class ApiUserUpdate(ApiUserBase):
    password: Optional[str] = None


class ApiUserInDBBase(ApiUserBase):
    id: int | None = None

    class Config:
        orm_mode = True


# Additional properties to return via API
class ApiUser(ApiUserInDBBase):
    pass


# Additional properties stored in DB
class ApiUserInDB(ApiUserInDBBase):
    hashed_password: str
