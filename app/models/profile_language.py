from sqlalchemy import Column, Integer, DateTime, Boolean, String,ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from datetime import datetime

class ProfileLanguage(Base):
    __tablename__= "profile_languages"
    
    id                          =   Column(Integer, primary_key=True, index=True)
    language_name               =   Column(String(255), nullable=False)
    language_code               =   Column(String(10), nullable=False)
    profile_request_id          =   Column(Integer, ForeignKey('profile_requests.id', ondelete='cascade'), nullable=False)
    created_at                  =   Column(DateTime, nullable=False, default=datetime.now())
    updated_at                  =   Column(DateTime, nullable=True, default=None)

    profile_request             =   relationship("ProfileRequest", back_populates="languages")