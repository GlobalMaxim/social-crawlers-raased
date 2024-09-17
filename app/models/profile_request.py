from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, DateTime, Boolean, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class ProfileRequest(Base):
    __tablename__= "profile_requests"
    
    id                          =   Column(Integer, primary_key=True, index=True)
    reply_link                  =   Column(String(255), nullable=False)
    external_id                 =   Column(Integer, nullable=False)
    first_name                  =   Column(String(255), nullable=True)
    last_name                   =   Column(String(255), nullable=True)
    date_of_birth               =   Column(DateTime, nullable=True)
    country_of_origin_code      =   Column(String(3), nullable=True)
    country_of_residence_code   =   Column(String(3), nullable=True)
    occupation                  =   Column(String(255), nullable=True)
    last_autocomplete_date      =   Column(DateTime, nullable=True)
    is_active                   =   Column(Boolean, nullable=False, default=True)
    created_at                  =   Column(DateTime, nullable=False, default=datetime.now())
    deleted_at                  =   Column(DateTime, nullable=True, default=None)
    updated_at                  =   Column(DateTime, nullable=True, default=None)
    
    languages                   =   relationship("ProfileLanguage", cascade="all, delete", passive_deletes=True, back_populates="profile_request")
    messengers                  =   relationship("ProfileMessenger", cascade="all, delete", passive_deletes=True, back_populates="profile_request")
    requests_links              =   relationship("ProfileRequestLink", cascade="all, delete", passive_deletes=True, back_populates="profile_request")
    emails                      =   relationship("ProfileEmail", cascade="all, delete", passive_deletes=True, back_populates="profile_request")
    addresses                   =   relationship("ProfileAddress", cascade="all, delete", passive_deletes=True, back_populates="profile_request")
    nicknames                   =   relationship("ProfileNickname", cascade="all, delete", passive_deletes=True, back_populates="profile_request")
    phones                      =   relationship("ProfilePhone", cascade="all, delete", passive_deletes=True, back_populates="profile_request")