from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, DateTime, Boolean, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class ProfileMessenger(Base):
    __tablename__= "profile_messengers"
    
    id                          =   Column(Integer, primary_key=True, index=True)
    account                     =   Column(String(255), nullable=False)
    messenger_name              =   Column(String(255), nullable=False)
    profile_request_id          =   Column(Integer, ForeignKey('profile_requests.id', ondelete="cascade"), nullable=False)
    created_at                  =   Column(DateTime, nullable=False, default=datetime.now())
    updated_at                  =   Column(DateTime, nullable=True, default=None)

    profile_request             =   relationship("ProfileRequest", back_populates="messengers")