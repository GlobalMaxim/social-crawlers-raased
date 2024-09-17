from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.mysql import LONGTEXT

from app.db.base_class import Base
from sqlalchemy.orm import relationship


class SocialParsingPost(Base):
    __tablename__ = "social_parsing_posts"

    id                =    Column(Integer, primary_key=True, index=True)
    external_id       =    Column(Integer, nullable=True, default=None)
    social_request_id =    Column(Integer, nullable=False)
    link_id           =    Column(Integer, nullable=True, default=None)
    smm_id            =    Column(Integer, nullable=True, default=None)
    account_name      =    Column(String(255), nullable=True, default=None)
    account_login     =    Column(String(255), nullable=True, default=None)
    post_name         =    Column(String(255), nullable=True, default=None)
    title             =    Column(Text(1000),nullable=True, default=None)
    description       =    Column(Text,nullable=True, default=None)
    content           =    Column(LONGTEXT, nullable=True, default=None)
    featured_image    =    Column(Text,nullable=True, default=None)
    video_image       =    Column(Text,nullable=True, default=None)
    source_link       =    Column(Text,nullable=True, default=None)
    is_storie         =    Column(Boolean, nullable=False, default=False)
    is_updated        =    Column(Boolean, nullable=False, default=False)
    crawler_name      =    Column(String(255), nullable=True, default=None)
    date_of_news      =    Column(DateTime, nullable=True, default=None)
    created_at        =    Column(DateTime, nullable=False)
    updated_at        =    Column(DateTime, nullable=True, default=None)

    social_posts_attachments = relationship("SocialPostAttachment")
    social_posts_reactions   = relationship("SocialPostReaction")
    social_posts_stats       = relationship("SocialPostStat", uselist=False, back_populates="social_parsing_post")
    social_requests          = relationship("SocialPostRequest", back_populates="social_parsing_post")
    # social_request           = relationship("SocialRequest", back_populates="social_parsing_posts")


