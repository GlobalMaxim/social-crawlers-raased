from datetime import datetime
from enum import Enum
from sqlalchemy import Column, ForeignKey, Integer, DateTime, Boolean, String
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import ENUM
from app.db.base_class import Base

class LinkType(str, Enum):
    WEB = 'WEB'
    SOCIAL = 'SOCIAL'
    YOUTUBE = 'YOUTUBE'

class ProfileRequestLink(Base):
    __tablename__= "profile_requests_links"
    
    id                          =   Column(Integer, primary_key=True, index=True)
    profile_request_id          =   Column(Integer, ForeignKey('profile_requests.id', ondelete="cascade"),nullable=False)
    profile_link_id             =   Column(Integer, ForeignKey('profile_links.id', ondelete="CASCADE"), nullable=False)
    is_associative              =   Column(Boolean,nullable=False, default=False)
    link_type                   =   Column(ENUM(LinkType), nullable=False)   
    created_at                  =   Column(DateTime, nullable=False, default=datetime.now())
    updated_at                  =   Column(DateTime, nullable=True, default=None)
    
    link                        =   relationship("ProfileLink", cascade="all, delete", passive_deletes=True, back_populates="requests_links")
    profile_request             =   relationship("ProfileRequest", cascade="all, delete", passive_deletes=True, back_populates="requests_links")