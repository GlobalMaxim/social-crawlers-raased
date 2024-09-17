from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class SocialPostRequest(Base):
    __tablename__ = "social_posts_requests"

    # id                        =    Column(Integer, primary_key=True, index=True)
    # external_id               =    Column(Integer, nullable=True, default=None)
    social_request_id           =    Column(Integer, ForeignKey("social_requests.id"), primary_key=True)
    social_parsing_post_id      =    Column(Integer, ForeignKey("social_parsing_posts.id"), primary_key=True)
    # created_at                =    Column(DateTime, nullable=False)
    # updated_at                =    Column(DateTime, nullable=True, default=None)
    
    social_parsing_post         =    relationship("SocialParsingPost", back_populates="social_requests")
    social_request              =    relationship("SocialRequest", back_populates="social_parsing_posts")