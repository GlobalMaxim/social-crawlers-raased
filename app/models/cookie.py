from sqlalchemy import Column, ForeignKey, DateTime, Boolean, String
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base


UInteger = INTEGER(unsigned=True)


class Cookie(Base):
    __tablename__ = "cookies"

    id                          =    Column(UInteger, primary_key=True)
    cookies_file                =    Column(String(255), nullable=False)
    account_id                  =    Column(UInteger, ForeignKey('social_accounts.id') , nullable=False)
    proxy_id                    =    Column(UInteger, nullable=True, default=None)
    is_valid                    =    Column(Boolean, nullable=False, default=True)
    is_locked                   =    Column(Boolean, nullable=False, default=False)
    date_locked                 =    Column(DateTime, nullable=True)
    created_at                  =    Column(DateTime, nullable=False, default=datetime.now)
    updated_at                  =    Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    social_account              =    relationship("SocialAccount", back_populates="cookies")

