from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, DateTime, Boolean, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class ProfileEmail(Base):
    __tablename__= "profile_emails"
    
    id                          =   Column(Integer, primary_key=True, index=True)
    email                       =   Column(String(255), nullable=True)
    profile_request_id          =   Column(Integer, ForeignKey('profile_requests.id', ondelete='cascade'), nullable=False)
    created_at                  =   Column(DateTime, nullable=False, default=datetime.now())
    updated_at                  =   Column(DateTime, nullable=True, default=None)

    profile_request             =   relationship("ProfileRequest", back_populates="emails")