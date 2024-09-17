from sqlalchemy import Column, Integer, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class SocialPostAttachment(Base):
    __tablename__ = "social_posts_attachments"

    id                        =    Column(Integer, primary_key=True, index=True)
    external_id               =    Column(Integer, nullable=True, default=None)
    social_parsing_post_id    =    Column(Integer, ForeignKey("social_parsing_posts.id"))
    video_path                =    Column(String(255), nullable=True, default=None)
    image_path                =    Column(String(255), nullable=True, default=None)
    created_at                =    Column(DateTime, nullable=False)
    updated_at                =    Column(DateTime, nullable=True, default=None)

    # social_parsing_posts      =    relationship("SocialParsingPost", back_populates="social_posts_attachments")