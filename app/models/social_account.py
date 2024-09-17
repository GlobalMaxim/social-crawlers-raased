from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.dialects.mysql import INTEGER, FLOAT, ENUM
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base
from app.schemas.social_account import Gender


UInteger = INTEGER(unsigned=True)
UFloat = FLOAT(unsigned=True)


class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id                          =    Column(UInteger, primary_key=True)
    smm_id                      =    Column(UInteger, nullable=False)
    login                       =    Column(String(64), nullable=True, default=None)
    email                       =    Column(String(64), nullable=True, default=None)
    email_password              =    Column(String(64), nullable=True, default=None) 
    password                    =    Column(String(64), nullable=True, default=None)
    phone                       =    Column(String(64), nullable=True, default=None)
    first_name                  =    Column(String(64), nullable=True, default=None)
    last_name                   =    Column(String(64), nullable=True, default=None)
    user_agent                  =    Column(String(255), nullable=True, default=None)
    note                        =    Column(String(255), nullable=True, default=None) 
    gender                      =    Column(ENUM(Gender), nullable=True, default=None)
    country_iso                 =    Column(String(2), nullable=True, default=None)
    language_iso                =    Column(String(2), nullable=True, default=None)
    is_active                   =    Column(Boolean, nullable=False, default=True)
    is_twofactor                =    Column(Boolean, nullable=False, default=False)
    twofactor_token             =    Column(String(255), nullable=True, default=None)
    twofactor_recovery_codes    =    Column(String(255), nullable=True, default=None)
    bans_count                  =    Column(UInteger, nullable=False, default=0)
    captcha_count               =    Column(UInteger, nullable=False, default=0)
    quality_percent             =    Column(UFloat, nullable=False, default=50.0)
    created_at                  =    Column(DateTime, nullable=False, default=datetime.now)
    updated_at                  =    Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    cookies                     =    relationship("Cookie", back_populates="social_account")

