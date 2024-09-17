from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Boolean, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class ProfileOccupation(Base):
    __tablename__= "profile_occupations"
    
    id                          =   Column(Integer, primary_key=True, index=True)
    name                        =   Column(String(255), nullable=False)
    slug                        =   Column(String(255), nullable=False)
    created_at                  =   Column(DateTime, nullable=False, default=datetime.now())
    updated_at                  =   Column(DateTime, nullable=True, default=None)