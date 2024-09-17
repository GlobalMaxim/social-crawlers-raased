from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Boolean, String,ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class ProfileLink(Base):
    __tablename__= "profile_links"
    
    id                          =   Column(Integer, primary_key=True, index=True)
    link                        =   Column(String(255), nullable=False)
    smm_slug                    =   Column(String(255), nullable=True)                    
    created_at                  =   Column(DateTime, nullable=False, default=datetime.now())
    updated_at                  =   Column(DateTime, nullable=True, default=None)

    requests_links      =   relationship("ProfileRequestLink",cascade="all, delete", passive_deletes=True, back_populates="link")