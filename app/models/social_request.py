from sqlalchemy import Column, Integer, DateTime, Boolean, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class SocialRequest(Base):
    __tablename__= "social_requests"
    
    id                        =    Column(Integer, primary_key=True, index=True)
    external_id               =    Column(Integer, nullable=False)
    active                    =    Column(Boolean, nullable=False)                
    is_global_search          =    Column(Boolean, nullable=False)
    reply_link                =    Column(String(255), nullable=False)
    crawling_frequency        =    Column(Integer, nullable=False)
    crawling_start_date       =    Column(DateTime, nullable=False)
    crawling_end_date         =    Column(DateTime, nullable=False)
    crawling_last_run_date    =    Column(DateTime, nullable=True, default=None)
    created_at                =    Column(DateTime, nullable=False)
    updated_at                =    Column(DateTime, nullable=True, default=None)

    social_keywords       = relationship("SocialKeyword")
    social_hashtags       = relationship("SocialHashtag")
    social_links          = relationship("SocialLink")
    social_parsing_posts  = relationship("SocialPostRequest", back_populates="social_request")