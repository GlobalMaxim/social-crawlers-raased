from sqlalchemy import Boolean, Column, Integer, String

from app.db.base_class import Base


class ApiUser(Base):
    __tablename__ = "api_user"

    id                 =    Column(Integer, primary_key=True, index=True)
    full_name          =    Column(String(255), index=True)
    email              =    Column(String(255), unique=True, index=True, nullable=False)
    hashed_password    =    Column(String(255), nullable=False)
    is_active          =    Column(Boolean(), default=True)
    is_superuser       =    Column(Boolean(), default=False)
